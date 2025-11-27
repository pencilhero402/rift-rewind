import React from 'react'
import { Link } from 'react-router-dom';
import '../App.css'
import '../css/Navigation.css'

const Navigation = () => {
    return (
        <nav>
            <ul>
                <h1 style={{ marginTop: '-20px', color: 'white' }}>
                    <a href="/" style={{ textDecoration: 'none', color: 'inherit' }}>🐥</a>
                </h1>
            </ul>
            <ul className="btn">
                <li><Link to='/login' role='button'>Login</Link></li>
            </ul>
        </nav>
    )
}

export default Navigation