const apiUrl = "/api";

export const userService = {
    login,
    logout,
    registerUser,
    getUser
};


function getUser() {
    return JSON.parse(localStorage.getItem("user"))
}

function registerUser(username, password) {
    const requestOptions = {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    };

    return fetch(`${apiUrl}/users/register`, requestOptions)
        .then(handleResponse)
        .then(user => {
            console.log(user);
            // login successful if there's a user in the response
            if (user) {
                localStorage.setItem('user', JSON.stringify(user));
            }

            return user;
        });
}


function login(username, password) {
    const requestOptions = {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    };

    return fetch(`${apiUrl}/users/login`, requestOptions)
        .then(handleResponse)
        .then(user => {
            console.log(user);
            // login successful if there's a user in the response
            if (user) {
                localStorage.setItem('user', JSON.stringify(user));
            }

            return user;
        });
}


function logout() {
    // remove user from local storage to log user out

    const requestOptions = {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: null
    };

    fetch(`${apiUrl}/users/logout`, requestOptions)
        .then(d => {
            localStorage.removeItem('user');
        });
}


function handleResponse(response) {
    return response.text().then(text => {
        if (!response.ok) {
            if (response.status === 401) {
                // auto logout if 401 response returned from api
                logout();
            }

            const error = (data && data.message) || response.statusText;
            return Promise.reject(error);
        }

        const data = text && JSON.parse(text);

        return data;
    });
}