import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabaseClient'
import { v4 as uuidv4 } from 'uuid'

const Card = () => {
    const [cardData, setCardData] = useState(null)
    const [markedNumbers, setMarkedNumbers] = useState([])
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(true)
    const [deviceUuid, setDeviceUuid] = useState(null)

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
                        .single()

                    console.log('Update result:', { updatedCard, updateError })

                    if (updateError) {
                        console.error('Supabase update error:', updateError)
                        setError(`Errore DB: ${updateError.message}`)
                        setLoading(false)
                        return
                    }

                    if (!updatedCard) {
                        // Someone else claimed it between our read and update
                        console.warn('Card was not updated. It might be already claimed.')
                        setError('Questa cartella è stata appena presa da qualcun altro.')
                        setLoading(false)
                        return
                    }

                    setCardData(updatedCard)
                    setMarkedNumbers(updatedCard.marked_numbers || [])
                } else if (card.owner_uuid === uuid) {
                    // This is our card - load it
                    setCardData(card)
                    setMarkedNumbers(card.marked_numbers || [])
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
            }
        } catch (err) {
            console.error('Error updating card:', err)
            setMarkedNumbers(markedNumbers)
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
        <div className="min-h-screen bg-deep-twilight flex flex-col items-center justify-center px-3 py-3">
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
                                                    className="font-bold"
                                                    style={{
                                                        zIndex: 31,
                                                        color: '#000000',
                                                        fontSize: 'clamp(1.35rem, 4vw, 2.7rem)'
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
