import React, {useEffect, useState} from "react";
import TextField from "@material-ui/core/TextField";
import Button from "@material-ui/core/Button";


export default function UserList(props) {
    const socket = props.data.socket;
    const room = props.data.room;
    const user = props.data.user;

    const [users, setUsers] = useState([]);
    const [turn, setTurn] = useState("");

    useEffect(() => {
        // Register event handlers.
        socket.on("userList", (data) => {
            console.log(data);
            setUsers(data);
        });
    }, []);


    return <div className={"user-list-wrapper"}>
        <div>
            <h4>User list</h4>
        </div>
        <div className={"user-list-entries"}>
            {
                users.map((user, i) => {
                    return <div key={i}>
                        { user.turn ?
                            <div><b className={"current-turn"}>{user.name}</b></div>:
                            <div><b>{user.name}</b></div>
                        }
                        <div><i>{Math.round(user.elo)}</i> ({user.type})</div>
                    </div>
                })
            }
        </div>
    </div>
}