/**
 * Utility functions per performance optimization
 */

/**
 * Debounce function - ritarda l'esecuzione fino a quando non passano {delay}ms
 * senza nuove chiamate. Utile per ridurre UPDATE al database.
 *
 * @param {Function} func - Funzione da eseguire
 * @param {number} delay - Delay in millisecondi
 * @returns {Function} Funzione debounced
 */
export function debounce(func, delay) {
    let timeoutId = null

    return function debounced(...args) {
        if (timeoutId) {
            clearTimeout(timeoutId)
        }

        timeoutId = setTimeout(() => {
            func.apply(this, args)
            timeoutId = null
        }, delay)
    }
}

/**
 * Throttle function - esegue al massimo una volta ogni {limit}ms
 *
 * @param {Function} func - Funzione da eseguire
 * @param {number} limit - Limite in millisecondi
 * @returns {Function} Funzione throttled
 */
export function throttle(func, limit) {
    let inThrottle = false

    return function throttled(...args) {
        if (!inThrottle) {
            func.apply(this, args)
            inThrottle = true
            setTimeout(() => {
                inThrottle = false
            }, limit)
        }
    }
}

/**
 * Delay helper
 * @param {number} ms - Millisecondi di attesa
 * @returns {Promise}
 */
export const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * Random value tra min e max
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
export const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min
