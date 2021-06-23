import React from 'react';
import Main from "./Main";
import {BrowserRouter, HashRouter} from "react-router-dom";

export default function App() {


    return <div>
        <BrowserRouter>
            <Main/>
        </BrowserRouter>
    </div>
}
