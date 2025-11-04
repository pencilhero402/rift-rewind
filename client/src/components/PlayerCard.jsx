import '../css/PlayerCard.css'

const PlayerCard = ( {gameName, tagLine, puuid, summonerIconId, summonerLevel, lane } ) => {
    return (
        <article>
            <div className="cardBorder">
                <div className="player-card-top">
                    <img
                        src={`/assets/profileicon/${summonerIconId}.png`}
                        alt="Profile Icon"
                        width={100}
                        height={100}
                        onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = '/assets/profileicon/1.png'; // default icon
                        }}
                    />
                    <h1 style= {{color: "white" }}>{gameName}</h1>
                    <p style= {{color: "white" }}>#{tagLine}</p>
                    <div className="lane">
                        <p>Lane{lane}</p>
                    </div>
                </div>
                
            </div>
        </article>
    );
};

export default PlayerCard;