import { useEffect, useState } from 'react';
import WinRatePieChart from './WinRatePieChart';
import '../css/PlayerCard.css';

const PlayerCard = ( {gameName, tagLine, puuid, summonerIconId, summonerLevel, lane, tier, role, champions, winrate } ) => {
    const [loadingChampions, setLoadingChampions] = useState({});
    const [randomChampion, setRandomChampion] = useState(null);

    // Set primary/secondary role
    let roleObj = {"Primary" : "FLEX", "Secondary" : null};
    if (role) {
        roleObj = typeof role === "string" 
            ? JSON.parse(role) 
            : role;
    }

    // Loads all champion_loading_images for page
    useEffect(() => {
        fetch('/data/loading_images.json')
            .then(res => res.json())
            .then(data => setLoadingChampions(data));
    }, []);

    const getRandomChampionImage = (champName) => {
        // Returns a random image given champion name
        if (!loadingChampions[champName] || loadingChampions[champName].length === 0) return null;
        const images = loadingChampions[champName];
        const randomIndex = Math.floor(Math.random() * images.length);

        return `/assets/champion/loading/${images[randomIndex]}`; // path to your images
    };

    let championObj = {};
    try {
        championObj = typeof champions === "string" ? JSON.parse(champions) : champions;
    } catch (e) {
        console.warn("Invalid champion JSON:", champions);
    }

    const sortedChampions = Object.entries(championObj)
        .sort((a, b) => b[1] - a[1]); // sort descending

    const [topChampionName, topChampionValue] = sortedChampions[0]; // Display top champion loading in player card
    const myChampionNames = sortedChampions.map(entry => entry[0]);
    const myChampionValues = sortedChampions.map(entry => entry[1]);

    console.log(`Player's champions ${myChampionNames.length}: ${myChampionNames}`)

    // Loads a random image of player's top champion
    useEffect(() => {
        if (!loadingChampions || !topChampionName) return;
        const image = getRandomChampionImage(topChampionName);
        setRandomChampion(image);
    }, [loadingChampions, topChampionName]);

    console.log(`YOUR RANK: ${tier.toLowerCase()}`)
    return (
        <article>
            <div className="cardBorder">
                <div className="player-card-top">
                    <img
                        src={`/assets/profileicon/${summonerIconId}.png`}
                        alt="Profile Icon"
                        className="summoner-icon-image"
                        onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = '/assets/profileicon/1.png'; // default icon
                        }}
                    />
                    <h1>{gameName}</h1>
                    <p>#{tagLine}</p>
                    <div className="lane">
                        <p>{roleObj?.Primary ?? "FLEX"}{roleObj?.Secondary ? ` / ${roleObj.Secondary}` : ""}</p>
                    </div>
                </div>

                <div className="player-card-middle">
                    <img
                        src={randomChampion}
                        alt="Best Champion Icon"
                        className="loading-champion-image"
                        onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = "/assets/champion/loading/Aatrox_0.jpg";
                        }}
                    />
                    <div className="player-match-stats">
                        <div className="rank-row">
                            <h3>Rank: </h3>
                            <img
                                    src={`/assets/rankIcon/${tier.toLowerCase()}.png`}
                                    alt="Rank"
                                    className="rank-icon"
                                    onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.src = "/assets/rankIcon/bronze.png"
                                    }}
                                />
                        </div>
                        <div className="winrate-row">
                            <h3>Winrate: </h3>
                            <div className="winrate-donut-chart">
                                <WinRatePieChart winrate={winrate || 0} />
                            </div>
                        </div>
                        <div className="champions-row">
                            <h3>Champions:</h3>
                            <div className="champion-icons-container">
                                <img
                                    src={`/assets/champion/tiles/${topChampionName}_0.jpg`}
                                    alt="Profile Icon"
                                    className="best-champion-icon"
                                    onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.src = '/assets/champion/tiles/Aatrox_0.jpg'; // default icon
                                    }}
                                />
                                {myChampionNames.slice(1).map((championName) => (
                                    <img
                                        key={championName} // unique key for React
                                        src={`/assets/champion/tiles/${championName}_0.jpg`}
                                        alt={championName}
                                        className="champion-icon"
                                        onError={(e) => {
                                            e.target.onerror = null;
                                            e.target.src = '/assets/champion/tiles/Aatrox_0.jpg'; // fallback
                                        }}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
                
            </div>
        </article>
    );
};

export default PlayerCard;