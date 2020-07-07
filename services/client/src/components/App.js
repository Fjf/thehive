import React from 'react';
import Main from "./Main";
import {HashRouter} from "react-router-dom";

export default function App() {


    return <div>
        <HashRouter>
            <Main/>
        </HashRouter>
    </div>
}
