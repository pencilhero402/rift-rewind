import React, { useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import '../css/SearchPlayer.css'
import PlayersAPI from '../services/PlayersAPI';

const SearchPlayer = () => {
    const navigate = useNavigate();
    
    const [nameAndTag, setNameAndTag] = useState('')
    const [message, setMessage] = useState('')
    const [player, setPlayer] = useState('')
    const [matches, setMatches] = useState([])
    const [playerStats, setPlayerStats] = useState([])

    // 1️⃣ Fetch or create player
    const fetchOrCreatePlayer = async (name, tag) => {
        try {
            const player = await PlayersAPI.upsertPlayer({
                gameName: name,
                tagLine: tag
            });

            console.log("Player created/updated:", player);
            return player;
        } catch (err) {
            console.error("Failed to create/update player:", err);
            setMessage("Error fetching or creating player.");
            return null;
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const [name, tag] = nameAndTag.split('#').map(s => s.trim());
        if (!name || !tag) {
            setMessage("gameName or tagLine is empty.");
            return;
        }

        try {
            // 1️⃣ Player
            const player = await fetchOrCreatePlayer(name, tag);
            console.log(player)
            setPlayer(player);

            setMessage(`Player data ready: ${name}#${tag}`);
            navigate(`player/${name}/${tag}`, { state: { player } });
        } catch (error) {
            console.error("Unexpected error:", error);
            setMessage("An unexpected error occurred.");
        }
    };

    return (
        <div className="search">
            <div className="container">
                <div className="search__inner">
                    <div className="search__title">
                        <h1>Rift Rewind</h1>    
                    </div>
                    <div className="search__box" id="f1">
                        <form>
                            <div className="search-bar">
                                <div className="region-select">
                                    <label htmlFor="region" name="region'">
                                        <select id="region" name="region">
                                            <option value="NA">NA</option>
                                            <option value="EU">EU</option>
                                            <option value="KR">KR</option>
                                            <option value="JP">JP</option>
                                            <option value="OCE">OCE</option>
                                        </select>
                                    </label>
                                </div>
                                <div className="search-input-wrapper">
                                    <input id="t1" type="search" placeholder="melon#23333" maxLength="30" onChange={e => setNameAndTag(e.target.value)}></input>
                                    <button className="search-button" type="button" onClick={handleSubmit}>🔍</button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SearchPlayer;