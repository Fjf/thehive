import LoginRegister from "./LoginRegister";
import Game from "./Game";
import {Route} from "react-router-dom";
import React from "react";


export default function Main() {

    return <div>
        <Route path={"/"} exact component={LoginRegister} />
        <Route path={"/game"} exact component={Game} />
    </div>
}