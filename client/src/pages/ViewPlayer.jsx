import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom';
import '../css/ViewPlayer.css'
import PlayersAPI from '../services/PlayersAPI';
import PlayerCard from '../components/PlayerCard';
import MatchHistoryCard from '../components/MatchHistoryCard';

const ViewPlayer = () => {
    const { gameName, tagLine } = useParams();
    const [player, setPlayer] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPlayerData = async () => {
            try {
                const playerData = await PlayersAPI.getPlayerByNameAndTag({gameName: gameName, tagLine: tagLine})
                console.log(playerData)
                setPlayer(playerData);
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

    return (
        <div>
            <h1 style={{ color: "white", }}>ViewPlayer Page</h1>
            <PlayerCard 
                gameName={gameName}
                tagLine={tagLine}
                puuid={player.player.puuid}
                summonerIconId={player.player.summonerIconId}
                summonerLevel={player.player.summonerLevel}
            />
            <MatchHistoryCard/>
        </div>
    );
};

export default ViewPlayer;