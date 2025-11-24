import { useState } from 'react';
import { useParams } from 'react-router-dom';
import '../css/MatchHistoryCard.css';

const MatchHistoryCard = ( { matchHistory }) => {
    const { gameName } = useParams();
    const [expandedDate, setExpandedDate] = useState(null);

    const getPlayerProperty = (match, playerName, property) => {
        const participant = match.participants.find(p => p.player === playerName);
        if (!participant) return "N/A";
        return participant[property] ?? "N/A"; // safe fallback if property doesn't exist
    };

    const matchHistoryArray = Object.values(matchHistory);

    const parseGameCreation = (gameCreation) => {
        // Replace space with 'T' to make it ISO-compliant
        if (!gameCreation) return new Date(0);
        return new Date(gameCreation.replace(' ', 'T'));
    };

    const parseGameDuration = (gameDuration) => {
        const [minutes, seconds] = gameDuration.split(':').map(Number);
        // Replace 31:30 with 31min 30s
        return `${minutes}min ${seconds}sec`
    }

    const sortedHistory = [...matchHistoryArray].sort(
        (a, b) => parseGameCreation(b.gameCreation) - parseGameCreation(a.gameCreation)
    );

    // Group matches by day   
    const groupedByDate = sortedHistory.reduce((acc, match) => {
        const dateKey = parseGameCreation(match.gameCreation).toLocaleDateString();
            if (!acc[dateKey]) acc[dateKey] = [];
            acc[dateKey].push(match);
            return acc;
    }, {});

    const groupedEntries = Object.entries(groupedByDate).sort(
        ([a], [b]) => parseGameCreation(b) - parseGameCreation(a)
    );

    const toggleDate = (date) => {
        setExpandedDate((prev) => (prev === date ? null : date));
    };

    return (
        <article>
            <div className="match-history-container">
                <h1 style={{ color: "white", }}>Clash History</h1>
                {groupedEntries.length > 0 ? (
                    groupedEntries.map(([date, matches]) => (
                        <div key={date} className="match-day-group">
                            <div
                            className="match-day-header"
                            onClick={() => toggleDate(date)}
                            style={{
                                cursor: "pointer",
                                color: "white",
                                backgroundColor: "#222",
                                padding: "8px",
                                borderRadius: "4px",
                                marginBottom: "6px",
                            }}
                            >
                            <strong>{date}</strong> ({matches.length} matches)
                        </div>
                        <div className="match-container">
                            {expandedDate === date && (
                                <div className="match-day-details" style={{ paddingLeft: "1rem"}}>
                                    {matches.map((match, i) => {
                                        const outcome = getPlayerProperty(match, gameName, "outcome");
                                        const outcomeText = outcome === 1 || outcome === "1" ? "Victory" : "Defeat";
                                        const champion = getPlayerProperty(match, gameName, "champion")
                                        const summonerSpells = getPlayerProperty(match, gameName, "summonerSpells");
                                        const summonerRunes = getPlayerProperty(match, gameName, "runes");
                                        const playerKDA = getPlayerProperty(match, gameName, "kda");
                                        const items = getPlayerProperty(match, gameName, "items");
                                        const participants = match.participants
                                        const team1 = participants.filter(p => p.teamId === 100);
                                        const team2 = participants.filter(p => p.teamId === 200);

                                        console.log(team1)
                                        console.log(team2)

                                        return (
                                            <div
                                                key={i}
                                                className={`match-card ${outcomeText === "Victory" ? "win" : "lose"}`}
                                            >
                                                <div className="match-card-info">
                                                    <div className="match-card-info-lane">
                                                        <p><strong>{getPlayerProperty(match, gameName, "lane")}</strong></p>
                                                        <p><strong>{champion}</strong></p>
                                                    </div>
                                                    <div className="match-card-info-time">
                                                        <p><strong>Duration:</strong> {parseGameDuration(match.gameDuration)}</p>
                                                        <p><strong>Result:</strong> {outcomeText}</p>
                                                    </div>
                                                </div>

                                                <div className="match-card-player-container">
                                                    <div className="match-stats-container">
                                                        <img 
                                                            src={`/assets/champion/tiles/${champion}_0.jpg`}
                                                            className="circle medium"
                                                            onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                            }}
                                                        />
                                                        <div className="summoner-spells-container">
                                                            <img
                                                                src={`/assets/summonerSpellIcon/${summonerSpells[0]['0']}.jpg`}
                                                                className="circle small"
                                                                onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                                }}
                                                            />
                                                            <img
                                                                src={`/assets/summonerSpellIcon/${summonerSpells[0]['1']}.jpg`}
                                                                className="circle small"
                                                                onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                                }}
                                                            />
                                                        </div>
                                                        <div className="summoner-runes-container">
                                                            <img
                                                                src={`/assets/runeIcon/${summonerRunes['primary']}/${summonerRunes['keystone']}.png`}
                                                                className="circle small"
                                                                onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                                }}
                                                            />
                                                            <img
                                                                src={`/assets/runeIcon/${summonerRunes['secondary']}/_${summonerRunes['secondary']}.png`}
                                                                className="circle extra small"
                                                                onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                                }}
                                                            />
                                                        </div>
                                                        <div className="player-kda-container">
                                                            <p>
                                                                {playerKDA.deaths === 0 && playerKDA.kills > 0
                                                                    ? "PERFECT"
                                                                    : `${playerKDA.kda} KDA`}
                                                            </p>
                                                            <div style={{ display: "flex", }}>
                                                                <span style={{ color: "white" }}>{playerKDA.kills}/</span>
                                                                <span style={{ color: "red" }}>{playerKDA.deaths}</span>
                                                                <span style={{ color: "white" }}>/{playerKDA.assists}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="item-container">
                                                        <img
                                                            src={`/assets/item/${items['item0']}.png`}
                                                            className="square small"
                                                            onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                            }}
                                                        />
                                                        <img
                                                            src={`/assets/item/${items['item1']}.png`}
                                                            className="square small"
                                                            onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                            }}
                                                        />
                                                        <img
                                                            src={`/assets/item/${items['item2']}.png`}
                                                            className="square small"
                                                            onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                            }}
                                                        />
                                                        <img
                                                            src={`/assets/item/${items['item3']}.png`}
                                                            className="square small"
                                                            onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                            }}
                                                        />
                                                        <img
                                                            src={`/assets/item/${items['item4']}.png`}
                                                            className="square small"
                                                            onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                            }}
                                                        />
                                                        <img
                                                            src={`/assets/item/${items['item5']}.png`}
                                                            className="square small"
                                                            onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                            }}
                                                        />
                                                        <img
                                                            src={`/assets/item/${items['item6']}.png`}
                                                            className="square small"
                                                            onError={(e) => {
                                                                    e.target.onerror = null;
                                                                    e.target.src = "/player.png";
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="match-card-match-container">
                                                    <div className="team-container">
                                                        <h4 style={{ color: "white" }}>Team 1</h4>
                                                        {team1.map((player, i) => (
                                                            <div className="player-name-and-icon">
                                                                <img 
                                                                    src={`/assets/champion/tiles/${player.champion}_0.jpg`}
                                                                    className="square extra small"
                                                                    onError={(e) => {
                                                                            e.target.onerror = null;
                                                                            e.target.src = "/player.png";
                                                                    }}
                                                                />
                                                                <p style={{paddingLeft: '4px'}}>{player.player.length > 10 ? player.player.slice(0, 10) + "…" : player.player}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                    <div className="team-container">
                                                        <h4 style={{ color: "white" }}>Team 2</h4>
                                                        {team2.map((player, i) => (
                                                            <div className="player-name-and-icon">
                                                                <img 
                                                                    src={`/assets/champion/tiles/${player.champion}_0.jpg`}
                                                                    className="square extra small"
                                                                    onError={(e) => {
                                                                            e.target.onerror = null;
                                                                            e.target.src = "/player.png";
                                                                    }}
                                                                />
                                                                <p style={{paddingLeft: '4px'}}>{player.player.length > 7 ? player.player.slice(0, 10) + "…" : player.player}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                            </div>
                        )}
                    </div>
                </div>
            ))
            ) : (
                <p style={{ color: "white" }}>No match history found.</p>
            )}
        </div>
    </article>
    );
};

export default MatchHistoryCard;