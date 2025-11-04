const API_URL = 'http://localhost:5001/api/matches'
const MatchesAPI = {
    createMatches: async(playerData) => {
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

    getAllMatches: () => {
        
    },
};

export default MatchesAPI;