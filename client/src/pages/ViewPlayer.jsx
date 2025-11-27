import React, { useState, useEffect } from 'react'
import { useParams, useLocation } from 'react-router-dom';
import '../css/ViewPlayer.css'
import PlayersAPI from '../services/PlayersAPI';
import MatchHistoryAPI from '../services/MatchHistoryAPI';
import PlayerStatsAPI from '../services/PlayerStatsAPI';
import PlayerCard from '../components/PlayerCard';
import MatchHistoryCard from '../components/MatchHistoryCard';

const ViewPlayer = () => {
    const { gameName, tagLine } = useParams();
    const location = useLocation();
    const initialPlayer = location.state?.player || null;

    const [player, setPlayer] = useState(null);
    const [error, setError] = useState(null);
    const [playerHistory, setPlayerHistory] = useState([]);
    const [match, setMatchData] = useState([]);
    const [playerStats, setPlayerStats] = useState(null);


    useEffect(() => {
        const fetchPlayerData = async () => {
            try {
                // Fetch only if missing
                const playerPromise = player
                    ? Promise.resolve(player)
                    : PlayersAPI.getPlayerByNameAndTag({ gameName, tagLine });

                const [playerData, statsData, historyData] = await Promise.all([
                    playerPromise,
                    PlayerStatsAPI.getPlayerStats({ gameName, tagLine }),
                    MatchHistoryAPI.getMatchHistoryOfPlayer({ gameName, tagLine }),
                ]);

                setPlayer(playerData);
                setPlayerStats(statsData);
                setPlayerHistory(historyData);
            } catch (err) {
                console.error("Error fetching player data:", err);
                setError("Failed to load player data.");
            }
        };

        if (gameName && tagLine) {
            fetchPlayerData();
        } else {
            setError("Invalid player name or tag.");
        }
    }, [gameName, tagLine]);

    if (error) return <div>{error}</div>;
    if (!player) return <div>Loading player...</div>;
    console.log(player)

    return (
        <div>
            <PlayerCard 
                gameName={gameName}
                tagLine={tagLine}
                puuid={player.puuid}
                summonerIconId={player.summonerIconId}
                summonerLevel={player.summonerLevel}
                tier={player.tier || "Unranked"}
                role={playerStats?.role || {}}
                champions={playerStats?.topChampions || {}}
                winrate={playerStats?.winrate || "None"}
            />
            <MatchHistoryCard matchHistory={playerHistory || []} />
        </div>
    );
};

export default ViewPlayer;