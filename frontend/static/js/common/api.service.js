function getCookie(name) {
    const cookieString = document.cookie || "";
    const cookies = cookieString.split(";");
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith(name + "=")) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return null;
}

const ClubApi = {
    ajaxify(href, callback) {
        const csrfToken = getCookie("csrftoken");
        const params = {
            method: "POST",
            credentials: "include",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        };
        if (csrfToken) {
            params.headers["X-CSRFToken"] = csrfToken;
        }

        fetch(href + "?is_ajax=true", params)
            .then((response) => response.json())
            .then((data) => callback(data));
    },
};

export default ClubApi;
