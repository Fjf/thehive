import React, {useEffect, useState} from "react";
import TextField from "@material-ui/core/TextField";
import Button from "@material-ui/core/Button";
import {userService} from "./userService";
import {useCookies} from "react-cookie";


export default function LoginRegister(props) {

    const [cookies, setCookie, removeCookie] = useCookies(["loginData"]);
    const [loginData, setLoginData] = useState(
        cookies.loginData || {
            username: "",
            password: ""
        });

    function login() {
        const username = loginData.username;
        const password = loginData.password;

        if (username === "" || password === "")
            return;

        setCookie("loginData", loginData, {sameSite: "strict"});

        userService.login(username, password).then(r => {
            window.location.href = "/game";
        });
    }

    function register() {
        const username = loginData.username;
        const password = loginData.password;

        if (username === "" || password === "")
            return;

        setCookie("loginData", loginData);

        userService.registerUser(username, password).then(r => {
            window.location.href = "/game";
        });
    }

    return <div className={"login-wrapper"}>
        <div className={"login-menu"}>
            <h1>Login</h1>
            <TextField
                placeholder={"Username"}
                label={"Username"}
                value={loginData.username}
                onChange={(e) => {
                    setLoginData({
                        ...loginData,
                        username: e.target.value
                    });
                }}
            />
            <TextField
                type={"password"}
                label={"Password"}
                placeholder={"Password"}
                value={loginData.password}
                onChange={(e) => {
                    setLoginData({
                        ...loginData,
                        password: e.target.value
                    });
                }}
            />
            <div className={"row-data"}>
                <Button onClick={login}>
                    Login
                </Button>
                <Button onClick={register}>
                    Register
                </Button>
            </div>
        </div>
    </div>
}