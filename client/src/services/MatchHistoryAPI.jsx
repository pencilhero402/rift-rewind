const API_URL = 'https://4l4gk471mh.execute-api.us-east-1.amazonaws.com/prod/match-history'
const MatchesAPI = {
    getMatchHistoryOfPlayer: async (playerData) => {
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
            console.error(`Error fetching Player with Riot ID: ${playerData.gameName}#${playerData.tagLine}`)
            //throw(error)
        }
    },
};

export default MatchesAPI;