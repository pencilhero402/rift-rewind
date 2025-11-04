const API_URL = 'http://localhost:5001/api/players'
const PlayersAPI = {
    createPlayer: async(playerData) => {
        try {
            const requestBody = {
                gameName: playerData.gameName.trim(),
                tagLine: playerData.tagLine.trim()
            }
            const options = {
                method: 'POST',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody),
            }
            const response = await fetch(`${API_URL}`, options)
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json()
            return data
        } catch(error) {
            throw error
        }
    },

    getPlayerByNameAndTag: async (playerData) => {
        try {
            const response = await fetch(`${API_URL}/${playerData.gameName}/${playerData.tagLine}`)
            if (!response.ok) {
                throw new Error(`Player with name ${playerData.gameName} and ${playerData.tagLine} does not exist.`)
            }
            const data = await response.json()
            return data
        } catch(error) {
            console.error(`Error fetching Player with Riot ID: ${playerData.gameName}#${playerData.tagLine}`)
            throw(error)
        }
    },

    updatePlayer: async () => {
    },

        // Probably don't need
    getAllPlayers: async () => {
        try {
            const response = await fetch(API_URL);
            const data = await response.json();
            return data;
        } catch(error) {
            throw error;
        }
    },
};

export default PlayersAPI;