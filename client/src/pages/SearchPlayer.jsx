import React, { useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import '../css/SearchPlayer.css'
import PlayersAPI from '../services/PlayersAPI';
import MatchesAPI from '../services/MatchesAPI';

const SearchPlayer = () => {
    const navigate = useNavigate();
    
    const [nameAndTag, setNameAndTag] = useState('')
    const [message, setMessage] = useState('')

    const handleSubmit = async (e) => {
        e.preventDefault();

        const [name, tag] = nameAndTag.split('#').map(s => s.trim());
        if (!name || !tag) {
            setMessage("gameName or tagLine is empty.");
            return;
        }

        try {
            // 1️⃣ Try to find existing player
            const result = await PlayersAPI.getPlayerByNameAndTag({ gameName: name, tagLine: tag });
            if (result) {
                MatchesAPI.createMatches( {gameName:name, tagLine: tag } )
            }
            setMessage(`Found existing player ${name}#${tag}`);
            navigate(`player/${name}/${tag}`);
        } catch (error) {
            console.warn("Player not found, attempting to create new one...");
            console.error(error);

            // 2️⃣ Fallback: create player if not found
            try {
                const createResult = await PlayersAPI.createPlayer({ gameName: name, tagLine: tag });
                setMessage(`Created new player ${name}#${tag}`);
                navigate(`player/${name}/${tag}`);
            } catch (createError) {
                console.error("Failed to create player:", createError);
                setMessage("Failed to find or create player.");
            }
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