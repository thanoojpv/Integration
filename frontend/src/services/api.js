const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL


// =====================================================
// NORMALIZE API ENDPOINT
// =====================================================
//
// Supports all of these:
//
// /auth/login
// /api/auth/login
// auth/login
// api/auth/login
//
// Final result:
//
// /api/auth/login
// =====================================================

function normalizeEndpoint(endpoint) {

    if (!endpoint) {
        return '/api'
    }


    let normalizedEndpoint =
        String(endpoint).trim()


    // Make sure endpoint starts with /
    if (!normalizedEndpoint.startsWith('/')) {
        normalizedEndpoint =
            `/${normalizedEndpoint}`
    }


    // Already contains /api
    if (normalizedEndpoint === '/api') {
        return normalizedEndpoint
    }


    if (normalizedEndpoint.startsWith('/api/')) {
        return normalizedEndpoint
    }


    // Add /api
    return `/api${normalizedEndpoint}`
}


// =====================================================
// COMMON API REQUEST
// =====================================================

export async function apiRequest(
    endpoint,
    options = {}
) {

    const token =
        localStorage.getItem('access_token')


    const headers = {
        ...(options.headers || {})
    }


    // -------------------------------------------------
    // CONTENT TYPE
    // -------------------------------------------------
    //
    // Do NOT manually set Content-Type for FormData.
    // Browser creates the multipart boundary.
    // -------------------------------------------------

    if (
        !(options.body instanceof FormData)
    ) {

        headers['Content-Type'] =
            'application/json'

    }


    // -------------------------------------------------
    // AUTHORIZATION
    // -------------------------------------------------

    if (
        token &&
        !headers.Authorization
    ) {

        headers.Authorization =
            `Bearer ${token}`

    }


    // -------------------------------------------------
    // NORMALIZE ENDPOINT
    // -------------------------------------------------

    const normalizedEndpoint =
        normalizeEndpoint(endpoint)


    // -------------------------------------------------
    // FULL URL
    // -------------------------------------------------

    const url =
        `${API_BASE_URL}${normalizedEndpoint}`


    // -------------------------------------------------
    // REQUEST
    // -------------------------------------------------

    const response =
        await fetch(
            url,
            {
                ...options,
                headers
            }
        )


    // -------------------------------------------------
    // RESPONSE
    // -------------------------------------------------

    const data =
        await response
            .json()
            .catch(() => null)


    // -------------------------------------------------
    // ERROR
    // -------------------------------------------------

    if (!response.ok) {

        throw new Error(
            data?.message ||
            data?.error ||
            `Request failed (${response.status})`
        )

    }


    return data
}



// =====================================================
// AUTHENTICATED FILE / BLOB REQUEST
// =====================================================
//
// Used for:
//
// - Trainer viewing videos
// - Trainer viewing PDFs
// - Learner viewing videos
// - Learner viewing PDFs
// - Invoice PDF downloads
//
// Normal <a href=""> cannot send JWT.
// This function sends Authorization manually.
// =====================================================

export async function fetchAuthenticatedBlob(
    endpoint
) {

    const token =
        localStorage.getItem('access_token')


    if (!token) {

        throw new Error(
            'You are not logged in'
        )

    }


    // -------------------------------------------------
    // NORMALIZE ENDPOINT
    // -------------------------------------------------

    const normalizedEndpoint =
        normalizeEndpoint(endpoint)


    // -------------------------------------------------
    // FULL URL
    // -------------------------------------------------

    const url =
        `${API_BASE_URL}${normalizedEndpoint}`


    // -------------------------------------------------
    // REQUEST
    // -------------------------------------------------

    const response =
        await fetch(
            url,
            {
                method: 'GET',

                headers: {
                    Authorization:
                        `Bearer ${token}`
                }
            }
        )


    // -------------------------------------------------
    // ERROR
    // -------------------------------------------------

    if (!response.ok) {

        let message =
            'Unable to open resource'


        try {

            const data =
                await response.json()


            message =
                data?.error ||
                data?.message ||
                message

        } catch {

            // Ignore JSON parsing error

        }


        throw new Error(message)

    }


    // -------------------------------------------------
    // RETURN FILE
    // -------------------------------------------------

    return await response.blob()

}



// =====================================================
// LOGIN
// =====================================================

export async function loginUser(
    email,
    password
) {

    return apiRequest(
        '/api/auth/login',
        {
            method: 'POST',

            body: JSON.stringify({
                email,
                password
            })
        }
    )

}



// =====================================================
// REGISTER
// =====================================================

export async function registerUser(
    name,
    email,
    password
) {

    return apiRequest(
        '/api/auth/register',
        {
            method: 'POST',

            body: JSON.stringify({
                name,
                email,
                password
            })
        }
    )

}



// =====================================================
// CURRENT USER
// =====================================================

export async function getCurrentUser(
    token
) {

    return apiRequest(
        '/api/auth/me',
        {
            method: 'GET',

            headers: {
                Authorization:
                    `Bearer ${token}`
            }
        }
    )

}