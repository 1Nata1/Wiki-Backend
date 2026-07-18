// Configuração da API
// Altere esta URL quando fizer deploy do backend
const API_URL = window.location.origin + "/api";

function getToken() {
    return localStorage.getItem("wikiToken") || sessionStorage.getItem("wikiToken");
}

function getUsername() {
    return localStorage.getItem("wikiUsuario") || sessionStorage.getItem("wikiUsuario");
}

function getUserName() {
    return localStorage.getItem("wikiUsuarioNome") || sessionStorage.getItem("wikiUsuarioNome") || getUsername();
}

function setSession(token, username, nome, remember) {
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem("wikiToken", token);
    storage.setItem("wikiUsuario", username);
    storage.setItem("wikiUsuarioNome", nome);
}

function clearSession() {
    localStorage.removeItem("wikiToken");
    localStorage.removeItem("wikiUsuario");
    localStorage.removeItem("wikiUsuarioNome");
    sessionStorage.removeItem("wikiToken");
    sessionStorage.removeItem("wikiUsuario");
    sessionStorage.removeItem("wikiUsuarioNome");
}

function isLogado() {
    return !!getToken();
}

function getHeaders() {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
    return headers;
}

async function apiRegister(nome, username, email, password) {
    const res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, username, email, password })
    });
    return await res.json();
}

async function apiLogin(username, password) {
    const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
    return await res.json();
}

async function apiGetUser() {
    const res = await fetch(`${API_URL}/user`, { headers: getHeaders() });
    return await res.json();
}

async function apiGetComentarios(pagina = "wendy") {
    const token = getToken();
    let url = `${API_URL}/comentarios?pagina=${pagina}`;
    if (token) url += `&token=${token}`;
    const res = await fetch(url);
    return await res.json();
}

async function apiCriarComentario(texto, pagina = "wendy") {
    const res = await fetch(`${API_URL}/comentarios`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ texto, pagina, token: getToken() })
    });
    return await res.json();
}

async function apiAprovarComentario(id) {
    const res = await fetch(`${API_URL}/comentarios/${id}/aprovar`, {
        method: "PUT",
        headers: getHeaders(),
        body: JSON.stringify({ token: getToken() })
    });
    return await res.json();
}

async function apiExcluirComentario(id) {
    const res = await fetch(`${API_URL}/comentarios/${id}?token=${getToken()}`, {
        method: "DELETE",
        headers: getHeaders()
    });
    return await res.json();
}

async function apiListarUsuarios() {
    const res = await fetch(`${API_URL}/usuarios?token=${getToken()}`, { headers: getHeaders() });
    return await res.json();
}

async function apiPromoverModerador(usuarioId) {
    const res = await fetch(`${API_URL}/usuarios/${usuarioId}/promover`, {
        method: "PUT",
        headers: getHeaders(),
        body: JSON.stringify({ token: getToken() })
    });
    return await res.json();
}

async function apiRebaixarModerador(usuarioId) {
    const res = await fetch(`${API_URL}/usuarios/${usuarioId}/rebaixar`, {
        method: "PUT",
        headers: getHeaders(),
        body: JSON.stringify({ token: getToken() })
    });
    return await res.json();
}
