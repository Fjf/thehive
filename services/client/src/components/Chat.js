import React, {useEffect, useState} from "react";
import TextField from "@material-ui/core/TextField";
import Button from "@material-ui/core/Button";




export default function Chat(props) {
    const socket = props.data.socket;
    const room = props.data.room;
    const user = props.data.user;

    const [messages, setMessages] = useState([]);
    const [message, setMessage] = useState("");

    useEffect(() => {
        // Register event handlers.
        socket.on("chatMessage", (data) => {
            setMessages(messages => [...messages, data]);
        });
    }, []);

    function sendMessageButton() {
        if (message === "") return;
        let data = {
            room: room,
            user: user,
            data: {name: user, message: message}
        };
        socket.emit("chatMessage", data);
        setMessage("");
    }

    return <div className={"chat-wrapper"}>
        <div className={"chat-messages"}>
            {
                messages.map((data, i) => {
                    return <div key={i}>
                        <b>{data.name}:</b> {data.message}
                    </div>
                })
            }
        </div>
        <div className={"chat-bar"}>
            <TextField
                style={{flex: 3}}
                label={"Message"}
                value={message}
                onChange={(event) => setMessage(event.target.value)}
            >
            </TextField>
            <Button
                style={{flex: 1, height: "auto"}}
                variant={"contained"}
                onClick={sendMessageButton}
            >Send</Button>
        </div>
    </div>
}