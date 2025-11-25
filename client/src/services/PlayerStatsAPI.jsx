const API_URL = import.meta.env.VITE_PLAYER_STATS_API_PATH;
const PlayerStatsAPI = {
    createPlayerStats: async(playerData) => {
        try {
            const puuid = playerData.puuid.trim()

            const requestBody = {
                action: "create_player_stats",
                puuid: puuid,
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
            console.error(`Player does not exist.`)
            throw error
        }
    },

    getPlayerStats: async(playerData) => {
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
};

export default PlayerStatsAPI;