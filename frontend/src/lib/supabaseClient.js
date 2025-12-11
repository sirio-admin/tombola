import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase environment variables')
}

// Configurazione ottimizzata per 100+ utenti simultanei
const supabaseOptions = {
    auth: {
        persistSession: false, // Non necessitiamo auth tradizionale
        autoRefreshToken: false,
    },
    db: {
        schema: 'public',
    },
    global: {
        headers: {
            'x-client-info': 'tombola-app',
        },
    },
    // Retry configuration per gestire picchi di carico
    realtime: {
        params: {
            eventsPerSecond: 10, // Limita eventi realtime se usati
        },
    },
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, supabaseOptions)

/**
 * Retry logic con exponential backoff per operazioni critiche
 * @param {Function} operation - Funzione async da eseguire con retry
 * @param {number} maxRetries - Numero massimo di tentativi (default: 3)
 * @param {number} baseDelay - Delay iniziale in ms (default: 300)
 * @returns {Promise} Risultato dell'operazione
 */
export async function withRetry(operation, maxRetries = 3, baseDelay = 300) {
    let lastError = null

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const result = await operation()
            return result
        } catch (error) {
            lastError = error

            // Non fare retry su errori 4xx (client errors)
            if (error?.status >= 400 && error?.status < 500) {
                throw error
            }

            // Ultimo tentativo fallito
            if (attempt === maxRetries - 1) {
                throw error
            }

            // Exponential backoff con jitter
            const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 100
            console.warn(`Retry ${attempt + 1}/${maxRetries} dopo ${delay.toFixed(0)}ms`, error)

            await new Promise(resolve => setTimeout(resolve, delay))
        }
    }

    throw lastError
}
