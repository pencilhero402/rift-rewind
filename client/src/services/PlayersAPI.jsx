const API_URL = 'https://4l4gk471mh.execute-api.us-east-1.amazonaws.com/prod/player'
const PlayersAPI = {
    createOrUpdatePlayer: async(playerData) => {
        try {
            const gameName = playerData.gameName.trim();
            const tagLine = playerData.tagLine.trim();

            const requestBody = {
                gameName: gameName,
                tagLine: tagLine
            }

            const options = {
                method: 'POST',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody),
            };

            console.log(requestBody)

            const response = await fetch(API_URL, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || errorData.message || `Player not found`);
            }

            const data = await response.json()
            return data
        } catch(error) {
            console.error(`${playerData.gameName}#${playerData.tagLine} does not exist.`)
            throw error
        }
    },

    getPlayerByNameAndTag: async (playerData) => {
        try {
            const gameName = playerData.gameName.trim();
            const tagLine = playerData.tagLine.trim();

            const response = await fetch(`${API_URL}?gameName=${gameName}&tagLine=${tagLine}`)
            if (!response.ok) {
                throw new Error(`Player with name ${gameName} and ${tagLine} does not exist.`)
            }
            const data = await response.json()
            return data
        } catch(error) {
            console.error(`Attempting to create Player with Riot ID: ${playerData.gameName}#${playerData.tagLine}`)
            //throw(error)
        }
    },

    // Handles Request for All:
    // Player, Player Stats, MatchData, MatchTimeline
    upsertPlayer: async (playerData) => {
        try {
            const name = playerData.gameName.trim()
            const tag = playerData.tagLine.trim()

            const requestBody = {
                gameName: name,
                tagLine: tag
            }

            const options = {
                method: 'POST',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody),
            };

            console.log(requestBody)

            const response = await fetch(API_URL, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || errorData.message || `Player not found`);
            }
            const data = await response.json()
            return data
        } catch (error) {
            console.error(`${playerData.gameName}#${playerData.tagLine} does not exist.`)
            throw error
        }
    },

};

export default PlayersAPI;