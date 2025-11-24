import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom';
import '../css/ViewPlayer.css'
import PlayersAPI from '../services/PlayersAPI';
import MatchHistoryAPI from '../services/MatchHistoryAPI';
import PlayerStatsAPI from '../services/PlayerStatsAPI';
import PlayerCard from '../components/PlayerCard';
import MatchHistoryCard from '../components/MatchHistoryCard';

const ViewPlayer = () => {
    const { gameName, tagLine } = useParams();
    const [player, setPlayer] = useState(null);
    const [error, setError] = useState(null);
    const [playerHistory, setPlayerHistory] = useState([]);
    const [match, setMatchData] = useState([]);
    const [playerStats, setPlayerStats] = useState(null);

    useEffect(() => {
        const fetchPlayerData = async () => {
            try {
                const [playerData, playerStatsData, playerMatchHistoryData] = await Promise.all([
                    PlayersAPI.getPlayerByNameAndTag({ gameName: gameName, tagLine: tagLine }),
                    PlayerStatsAPI.getPlayerStats( { gameName: gameName, tagLine: tagLine } ),
                    MatchHistoryAPI.getMatchHistoryOfPlayer( { gameName: gameName, tagLine: tagLine}),
                ])
                console.log(playerData)
                console.log(playerStatsData)
                console.log(playerMatchHistoryData)

                setPlayer(playerData);
                setPlayerStats(playerStatsData);
                setPlayerHistory(playerMatchHistoryData);
            } catch (error) {
                console.error("Error fetching player data: ", error)
            }
        };
        if (gameName && tagLine) {
            fetchPlayerData();
        } else {
            setError("Invalid Player name and tag")
        }
    }, [gameName, tagLine]);

    if (error) {
        return <div>{error}</div>
    }
    
    if (!player) {
        return <div>Loading Player Details...</div>
    }
    console.log(player)

    return (
        <div>
            <h1 style={{ color: "white", }}>ViewPlayer Page</h1>
            <PlayerCard 
                gameName={gameName}
                tagLine={tagLine}
                puuid={player.puuid}
                summonerIconId={player.summonerIconId}
                summonerLevel={player.summonerLevel}
                tier={player?.tier || "Unranked"}
                role={playerStats?.role || {}}
                champions={playerStats?.topChampions || {}}
                winrate={playerStats?.winrate || "None"}
            />
            <MatchHistoryCard matchHistory={playerHistory || []} />
        </div>
    );
};

export default ViewPlayer;