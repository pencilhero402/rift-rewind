# Rift Rewind

## About

Rift Rewind is an advanced League of Legends performance tracker and match-history analysis tool. It helps players explore detailed insights about their gameplay, discover patterns, compare progress over time, and review full match timelines — all powered by modern AWS infrastructure and an AI analysis engine.

### Description and Purpose
Rift Rewind was built to give players a deeper understanding of how they perform across games. Unlike traditional match trackers, which only display static numbers, Rift Rewind analyzes how a player influences each game by combining raw match data, timeline events, role behavior, and AI-driven evaluations.

The platform answers questions such as:

How well do I lane compared to my role?

Where do I lose or gain advantages in the early game?

Which champions am I statistically best with?

What patterns appear across my match history?

The goal is to help players improve intelligently, not just read stats.

### Inspiration
The project was inspired by:

The lack of timeline-level insights on most public trackers

The difficulty of analyzing match data manually through the Riot API

The desire to build an AI-powered companion that explains performance

A passion for data-driven improvement in competitive games

Rift Rewind replays your matches from a data perspective — hence the name.

## Tech Stack

Frontend: React, HTML/CSS, Javascript

Backend: Python, AWS API Gateway, AWS RDS MySQL, AWS Lambda

## Features

### Data, Discovery & Interaction

Data, Discovery & Interaction

These features are available to all users to help them browse and explore player profiles:

Match History Search — look up any summoner and retrieve their latest matches

Match Timeline Viewer — inspect kills, CS, lane interactions, gold swings, and more

Player Statistics Dashboard — visualize champion pool, roles, winrates, and trends

AI Match Insights (Bedrock) — the system analyzes matches and summarizes key takeaways

Performance Breakdown — lane matchup scoring, early-game CS diff, objective activity

Cross-Match Trends — averages, consistency scores, and playstyle identity
