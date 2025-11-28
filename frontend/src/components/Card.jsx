import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabaseClient'
import { v4 as uuidv4 } from 'uuid'
import Confetti from 'react-confetti'
import { Fireworks } from '@fireworks-js/react'

const Card = () => {
    const [cardData, setCardData] = useState(null)
    const [markedNumbers, setMarkedNumbers] = useState([])
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(true)
    const [deviceUuid, setDeviceUuid] = useState(null)
    const [isWinner, setIsWinner] = useState(false)
    const [windowSize, setWindowSize] = useState({ width: window.innerWidth, height: window.innerHeight })

    useEffect(() => {
        const handleResize = () => {
            setWindowSize({ width: window.innerWidth, height: window.innerHeight })
        }
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [])

    useEffect(() => {
        const initializeCard = async () => {
            try {
                // 1. Get or create device UUID
                let uuid = localStorage.getItem('device_uuid')
                if (!uuid) {
                    uuid = uuidv4()
                    localStorage.setItem('device_uuid', uuid)
                }
                setDeviceUuid(uuid)

                // 2. Get card_id from URL or check for random assignment
                const urlParams = new URLSearchParams(window.location.search)
                const cardIdParam = urlParams.get('card_id')
                const cardId = cardIdParam ? parseInt(cardIdParam, 10) : null
                const isRandom = urlParams.get('random') === 'true'

                // Handle random card assignment
                if (isRandom) {
                    console.log('Random card assignment requested')

                    // Get multiple available cards to pick randomly from
                    const { data: availableCards, error: searchError } = await supabase
                        .from('cards')
                        .select('id')
                        .is('owner_uuid', null)
                        .limit(50)  // Get 50 cards to randomly choose from

                    if (searchError || !availableCards || availableCards.length === 0) {
                        setError('Nessuna cartella disponibile. Tutte le cartelle sono già state assegnate!')
                        setLoading(false)
                        return
                    }

                    // Pick a truly random card from available ones
                    const randomIndex = Math.floor(Math.random() * availableCards.length)
                    const randomCardId = availableCards[randomIndex].id
                    console.log(`Assigning random card ${randomCardId} (selected from ${availableCards.length} available)`)

                    // Claim the card immediately
                    const { data: claimedCard, error: claimError } = await supabase
                        .from('cards')
                        .update({ owner_uuid: uuid })
                        .eq('id', randomCardId)
                        .is('owner_uuid', null) // Double-check it's still available
                        .select()
                        .single()

                    if (claimError || !claimedCard) {
                        // Card was taken by someone else, try again
                        console.warn('Card claimed by someone else, retrying...')
                        window.location.reload()
                        return
                    }

                    // Redirect to the assigned card
                    window.location.href = `?card_id=${randomCardId}`
                    return
                }

                if (!cardId || isNaN(cardId)) {
                    setError('Nessuna cartella specificata o ID non valido. Scansiona un QR code valido.')
                    setLoading(false)
                    return
                }

                // 3. Fetch card from Supabase
                const { data: card, error: fetchError } = await supabase
                    .from('cards')
                    .select('*')
                    .eq('id', cardId)
                    .maybeSingle()

                if (fetchError) {
                    setError(`Errore DB: ${fetchError.message}`)
                    setLoading(false)
                    return
                }

                if (!card) {
                    setError('Cartella non trovata.')
                    setLoading(false)
                    return
                }

                // 4. Check ownership and claim if necessary
                if (card.owner_uuid === null) {
                    // Card is unclaimed - claim it!
                    console.log(`Attempting to claim card ${cardId} for uuid ${uuid}`)

                    // Use a more robust update query
                    const { data: updatedCard, error: updateError } = await supabase
                        .from('cards')
                        .update({ owner_uuid: uuid })
                        .eq('id', cardId)
                        .is('owner_uuid', null) // Ensure it's still unclaimed
                        .select()
                        .maybeSingle()

                    console.log('Update result:', { updatedCard, updateError })

                    if (updateError) {
                        console.error('Supabase update error:', updateError)
                        setError(`Errore DB: ${updateError.message}`)
                        setLoading(false)
                        return
                    }

                    if (!updatedCard) {
                        // The update didn't affect any rows. This implies the card is no longer 'owner_uuid IS NULL'.
                        // Check if WE own it (e.g., double-fire in StrictMode or race condition).
                        const { data: currentCardOwner } = await supabase
                            .from('cards')
                            .select('owner_uuid')
                            .eq('id', cardId)
                            .maybeSingle()
                        
                        if (currentCardOwner && currentCardOwner.owner_uuid === uuid) {
                             // It's ours! The previous attempt must have succeeded.
                             // Fetch the full card data to display it.
                             const { data: myCard } = await supabase
                                .from('cards')
                                .select('*')
                                .eq('id', cardId)
                                .single()
                             
                             setCardData(myCard)
                             setMarkedNumbers(myCard.marked_numbers || [])
                             // Check initial win state
                             if (myCard.marked_numbers && myCard.marked_numbers.length === 15) {
                                 setIsWinner(true)
                             }
                             setLoading(false)
                             return
                        }

                        // Someone else claimed it
                        console.warn('Card was not updated. It might be already claimed.')
                        setError('Questa cartella è stata appena presa da qualcun altro.')
                        setLoading(false)
                        return
                    }

                    setCardData(updatedCard)
                    setMarkedNumbers(updatedCard.marked_numbers || [])
                    if (updatedCard.marked_numbers && updatedCard.marked_numbers.length === 15) {
                         setIsWinner(true)
                    }
                } else if (card.owner_uuid === uuid) {
                    // This is our card - load it
                    setCardData(card)
                    setMarkedNumbers(card.marked_numbers || [])
                    if (card.marked_numbers && card.marked_numbers.length === 15) {
                         setIsWinner(true)
                    }
                } else {
                    // Card belongs to someone else
                    setError('Questa cartella è già stata presa da un altro dispositivo.')
                    setLoading(false)
                    return
                }

                setLoading(false)
            } catch (err) {
                console.error('Error initializing card:', err)
                setError('Errore di connessione. Riprova.')
                setLoading(false)
            }
        }

        initializeCard()
    }, [])

    const toggleNumber = async (number) => {
        if (!cardData) return

        const newMarkedNumbers = markedNumbers.includes(number)
            ? markedNumbers.filter(n => n !== number)
            : [...markedNumbers, number]

        // Optimistic UI update
        setMarkedNumbers(newMarkedNumbers)
        
        // Check for win
        if (newMarkedNumbers.length === 15) {
            setIsWinner(true)
        } else {
            setIsWinner(false)
        }

        // Update in Supabase
        try {
            const { error: updateError } = await supabase
                .from('cards')
                .update({ marked_numbers: newMarkedNumbers })
                .eq('id', cardData.id)
                .eq('owner_uuid', deviceUuid)

            if (updateError) {
                console.error('Error updating marked numbers:', updateError)
                // Revert on error
                setMarkedNumbers(markedNumbers)
                // Revert win state if needed, though rare
                setIsWinner(markedNumbers.length === 15)
            }
        } catch (err) {
            console.error('Error updating card:', err)
            setMarkedNumbers(markedNumbers)
            setIsWinner(markedNumbers.length === 15)
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-deep-twilight flex items-center justify-center p-4">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-4 border-lavender border-t-transparent mx-auto mb-4"></div>
                    <p className="text-white-custom text-xl font-semibold">Caricamento...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-deep-twilight flex items-center justify-center p-4">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 max-w-md text-center border border-white/20">
                    <div className="text-6xl mb-4">⚠️</div>
                    <h2 className="text-2xl font-bold text-white-custom mb-3">Ops!</h2>
                    <p className="text-white-custom/90 text-lg">{error}</p>
                </div>
            </div>
        )
    }

    if (!cardData) return null

    return (
        <div className="min-h-screen bg-deep-twilight flex flex-col items-center justify-center px-3 py-3 relative overflow-hidden">
            {isWinner && (
                <>
                    <Fireworks
                        options={{
                            opacity: 0.5,
                            particles: 200, // High particle count
                            explosion: 7,   // Intensity of explosion
                            intensity: 40,  // Frequency of fireworks
                            friction: 0.96, // Gravity/decay
                            gravity: 1.2,
                            acceleration: 1.02,
                            delay: { min: 15, max: 30 },
                            rocketsPoint: { min: 0, max: 100 }, // Launch from entire bottom width
                            lineWidth: { explosion: { min: 1, max: 4 }, trace: { min: 0.1, max: 1 } },
                            brightness: { min: 50, max: 80, decay: { min: 0.015, max: 0.03 } },
                        }}
                        style={{
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            position: 'fixed',
                            zIndex: 40, // Behind the modal (z-50) but above page
                            pointerEvents: 'none',
                        }}
                    />
                    <Confetti
                        width={windowSize.width}
                        height={windowSize.height}
                        recycle={true}
                        numberOfPieces={200}
                    />
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-md p-2 md:p-4 transition-all duration-500 overflow-y-auto">
                        <div 
                            className="relative rounded-[2rem] md:rounded-[3rem] shadow-2xl w-full max-w-[95vw] md:max-w-7xl flex flex-row items-center justify-between md:justify-center gap-2 md:gap-16 p-4 pb-16 md:p-20 md:pb-32 overflow-hidden border border-white/10"
                            style={{ 
                                background: 'linear-gradient(135deg, #07094A 0%, #1e3a8a 50%, #DCDCEF 100%)', 
                                boxShadow: '0 25px 80px -10px rgba(0, 0, 0, 0.7)'
                            }}
                        >
                             {/* Sfondo decorativo */}
                             <div className="absolute top-0 right-0 w-40 h-40 md:w-96 md:h-96 bg-white/5 rounded-full blur-3xl -mr-10 -mt-10 md:-mr-32 md:-mt-32 pointer-events-none"></div>
                             <div className="absolute bottom-0 left-0 w-40 h-40 md:w-80 md:h-80 bg-blue-400/10 rounded-full blur-3xl -ml-10 -mb-10 md:-ml-20 md:-mb-20 pointer-events-none"></div>

                            {/* Trofeo Sinistra - Sempre visibile a lato */}
                            <div 
                                className="relative z-10 filter drop-shadow-2xl animate-[bounce_2s_infinite] leading-none flex-shrink-0 select-none origin-center"
                                style={{ 
                                    fontSize: 'clamp(4rem, 14vw, 10rem)', // Reduced size by ~20%
                                    marginRight: '-0.5rem' 
                                }}
                            >
                                🏆
                            </div>
                            
                            {/* Contenitore Centrale */}
                            <div className="relative z-20 flex flex-col items-center text-center flex-grow w-full min-w-0 px-1">
                                <h1 className="text-3xl sm:text-5xl md:text-7xl lg:text-9xl font-black tracking-wider uppercase mb-4 md:mb-8 text-white drop-shadow-xl leading-tight whitespace-nowrap">
                                    HAI VINTO!
                                </h1>
                                
                                <button 
                                    onClick={() => setIsWinner(false)}
                                    className="group transition-all duration-300 transform hover:-translate-y-2 hover:shadow-2xl active:scale-95"
                                    style={{
                                        background: '#ffffff',
                                        color: '#07094A',
                                        padding: '0.8rem 2rem',
                                        fontSize: '1rem',
                                        fontWeight: '800',
                                        borderRadius: '9999px',
                                        border: 'none',
                                        cursor: 'pointer',
                                        letterSpacing: '0.1em',
                                        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
                                    }}
                                >
                                    <span className="md:hidden">CONTROLLA</span>
                                    <span className="hidden md:inline text-xl px-4 py-1">CONTROLLA</span>
                                </button>
                            </div>

                            {/* Trofeo Destra - Sempre visibile a lato */}
                            <div 
                                className="relative z-10 filter drop-shadow-2xl animate-[bounce_2s_infinite] leading-none flex-shrink-0 select-none delay-100 origin-center"
                                style={{ 
                                    fontSize: 'clamp(4rem, 14vw, 10rem)', // Reduced size by ~20%
                                    marginLeft: '-0.5rem'
                                }}
                            >
                                🏆
                            </div>
                        </div>
                    </div>
                </>
            )}

            <div className="card-shell">
                <div className="card-container">

                    <div className="card-background" aria-hidden="true" />

                    <div className="card-grid">
                        {cardData.numbers.map((row, rowIndex) => (
                            <div key={rowIndex} className="card-grid-row">
                                {row.map((number, colIndex) => (
                                    <div
                                        key={`${rowIndex}-${colIndex}`}
                                        className="relative flex items-center justify-center shadow-lg rounded-xl transition-all duration-200 select-none"
                                        style={{
                                            zIndex: 30,
                                            backgroundColor: 'rgba(255, 255, 255, 0.88)',
                                            border: '2px solid rgba(229, 231, 235, 0.95)',
                                            borderRadius: '12px',
                                            cursor: number ? 'pointer' : 'default',
                                            aspectRatio: '1 / 1'
                                        }}
                                        onClick={() => number && toggleNumber(number)}
                                    >
                                        {number && (
                                            <>
                                                <span
                                                    className="font-bold card-number-text"
                                                    style={{
                                                        zIndex: 31
                                                    }}
                                                >
                                                    {number}
                                                </span>
                                                {markedNumbers.includes(number) && (
                                                    <>
                                                        {/* X Diagonale Rossa - Prima linea (contenuta dentro la cella) */}
                                                        <div
                                                            className="absolute pointer-events-none"
                                                            style={{
                                                                transform: 'rotate(45deg)',
                                                                zIndex: 32,
                                                                top: '50%',
                                                                left: '50%',
                                                                marginLeft: '-40%',
                                                                marginTop: '-2px',
                                                                width: '80%'
                                                            }}
                                                        >
                                                            <div
                                                                className="rounded-full"
                                                                style={{
                                                                    height: '5px',
                                                                    backgroundColor: '#DC2626'
                                                                }}
                                                            ></div>
                                                        </div>
                                                        {/* X Diagonale Rossa - Seconda linea (contenuta dentro la cella) */}
                                                        <div
                                                            className="absolute pointer-events-none"
                                                            style={{
                                                                transform: 'rotate(-45deg)',
                                                                zIndex: 32,
                                                                top: '50%',
                                                                left: '50%',
                                                                marginLeft: '-40%',
                                                                marginTop: '-2px',
                                                                width: '80%'
                                                            }}
                                                        >
                                                            <div
                                                                className="rounded-full"
                                                                style={{
                                                                    height: '5px',
                                                                    backgroundColor: '#DC2626'
                                                                }}
                                                            ></div>
                                                        </div>
                                                    </>
                                                )}
                                            </>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Card
