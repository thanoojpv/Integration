const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL

// =====================================================
// COMMON API REQUEST
// =====================================================

export async function apiRequest(endpoint, options = {}) {

    const token =
        localStorage.getItem('access_token')


    const headers = {
        ...(options.headers || {})
    }


    // -------------------------------------------------
    // IMPORTANT:
    // Do NOT manually set Content-Type for FormData.
    // Browser must set multipart/form-data boundary.
    // -------------------------------------------------

    if (!(options.body instanceof FormData)) {

        headers['Content-Type'] =
            'application/json'

    }


    if (token && !headers.Authorization) {

        headers.Authorization =
            `Bearer ${token}`

    }


    const response =
        await fetch(
            `${API_BASE_URL}${endpoint}`,
            {
                ...options,
                headers
            }
        )


    const data =
        await response
            .json()
            .catch(() => null)


    if (!response.ok) {

        throw new Error(
            data?.message ||
            data?.error ||
            'Request failed'
        )

    }


    return data
}



// =====================================================
// AUTHENTICATED FILE / BLOB REQUEST
// =====================================================
//
// Used for:
// - Trainer viewing videos
// - Trainer viewing PDFs
// - Learner viewing videos
// - Learner viewing PDFs
//
// Normal <a href=""> cannot send JWT.
// This function sends the Authorization header.
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


    const response =
        await fetch(
            `${API_BASE_URL}${endpoint}`,
            {
                method: 'GET',
                headers: {
                    Authorization:
                        `Bearer ${token}`
                }
            }
        )


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