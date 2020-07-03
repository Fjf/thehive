import React, {useEffect, useState} from 'react';
import {TextField} from '@material-ui/core';
import {HexGrid} from "./HexGrid";
import {useCookies} from 'react-cookie';
import socketIOClient from "socket.io-client";
import Button from "@material-ui/core/Button";
import Chat from "./Chat";
import IconButton from "@material-ui/core/IconButton";

// SocketIO data.
// const ENDPOINT = "http://localhost:5000";
const socket = socketIOClient();

function TileSelection(name, amount) {
    this.name = name;
    this.amount = amount;
}

let hexGrid = new HexGrid();

const chatData = {
    socket: socket
};

const initialTileNames = [
    new TileSelection("queen", 1),
    new TileSelection("spider", 2),
    new TileSelection("beetle", 2),
    new TileSelection("grasshopper", 3),
    new TileSelection("ant", 3),
    new TileSelection("mosquito", 1),
    new TileSelection("ladybug", 1)
];


export default function Game() {
    let board = React.useRef(null);
    const [tileNames, setTileNames] = useState(initialTileNames);

    const [cookies, setCookie, removeCookie] = useCookies(['username', 'room']);
    const [username, setUsername] = useState("");
    const [room, setRoom] = useState("");
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        // Register canvas and load resources.
        hexGrid.setCanvas(board.current);
        hexGrid.preloadResources(initialTileNames);

        // Initialize event handlers for mouse.
        document.addEventListener('mousedown', (ev) => hexGrid.handleMouseDown(ev));
        document.addEventListener('mousemove', (ev) => hexGrid.handleMouseMove(ev));
        document.addEventListener('mouseup', (ev) => hexGrid.handleMouseUp(ev));

        // Set refresh timer
        setInterval(() => hexGrid.update(), 1000 / 60);

        // Check if the user has used the site previously
        let un = cookies.username;
        let rm = cookies.room;
        if (rm !== undefined) {
            setRoom(rm);
            setUsername(un);

            connectGame(un, rm);
        }
    }, []);

    function buttonDisconnectGame() {
        // TODO: Implement server leave button function
        socket.emit("leave", {room: room});
    }

    function buttonConnectGame() {
        connectGame(username, room);
    }

    function connectGame(username, room) {
        if (room === "" || username === "") {
            return;
        }

        setCookie("username", username, {sameSite: "strict"});
        setCookie("room", room, {sameSite: "strict"});

        // Setup socket event listeners and join the selected room.
        socket.emit("join", {
            room: room,
            username: username
        });

        socket.on("boardState", (rawResponse) => {
            let response = JSON.parse(rawResponse);
            hexGrid.setBoardState(response, username);
        });

        socket.on("placeTile", (response) => {
            let data = response.data;

            // Create a tile on desired position
            let tile;
            if (response.username === username) {
                // Place my tile
                tile = hexGrid.makeTile(data.image, data.x, data.y, hexGrid.tileClickHandler);
                tile.mine = true;
                // Remove tile from cursor.
                hexGrid.selection = null;
            } else {
                // Place opponents tile.
                tile = hexGrid.makeTile(data.image, data.x, data.y, null);
                tile.mine = false;
                // Remove the hover mouse state.
                hexGrid.enemyMouseState.pos = null;
            }
            hexGrid.putTile(tile, data.x, data.y);
            hexGrid.audio_files["tile_sound_2"].currentTime = 0.0;
            hexGrid.audio_files["tile_sound_2"].play();
        });

        hexGrid.onTilePlaceHandler = (tile) => {
            socket.emit("placeTile", {
                room: room,
                username: username,
                data: tile
            });
        };

        socket.on("pickupTile", (response) => {
            let data = response.data;

            if (response.username === username) {
                // Make a copy of the tile data.
                let tile = hexGrid.getTile(data.x, data.y);
                hexGrid.selection = {
                    ...tile
                };
            }
            hexGrid.removeTile(data.x, data.y);
        });

        hexGrid.onTilePickupHandler = (tile) => {
            socket.emit("pickupTile", {
                room: room,
                username: username,
                data: tile
            });
        };

        socket.on("mouseHover", (data) => {
            // Remotely sent tiles are never your own.
            hexGrid.setEnemyHover(data);
        });

        setInterval(() => {
            // Send current mouse state if a tile is selected.
            if (hexGrid.selection === null) return;

            socket.emit("mouseHover", {
                    room: room,
                    username: username,
                    data: {
                        pos: {
                            x: hexGrid.mouseState.pos.x - hexGrid.offset.x,
                            y: hexGrid.mouseState.pos.y - hexGrid.offset.y,
                        },
                        tile: {
                            ...hexGrid.selection,
                            mine: false
                        }
                    }
                }
            )
        }, 1000 / 30);

        setIsConnected(true);
    }

    return <div className={"content-wrapper"}>
        <div id={"left-menu-column"}>
            <div className={"column-data"}>
                {isConnected ? "Connected" : "Disconnected"}
                <TextField
                    name={"username"}
                    variant={"outlined"}
                    label={"Username"}
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                />
                <TextField
                    name={"room"}
                    variant={"outlined"}
                    label={"Room"}
                    value={room}
                    onChange={(event) => setRoom(event.target.value)}
                />
                {!isConnected ? <Button onClick={buttonConnectGame} variant="contained">Connect</Button>
                    : <Button onClick={buttonDisconnectGame} variant="contained">Disconnect</Button>
                }
            </div>
            <Chat data={{
                ...chatData,
                user: username,
                room: room
            }}/>
        </div>
        <canvas ref={board} className={"canvas"} id={"canvas"}>
        </canvas>
        <div id={"tile-selection"}>
            {
                tileNames.map((tileSelection, i) => {
                    let srcName = "static/images/" + tileSelection.name + ".png";
                    return <div key={i}>
                        <div>{tileSelection.amount} {tileSelection.name}{tileSelection.amount !== 1 ? "s" : ""} left.</div>
                        <IconButton
                            variant={"contained"}
                            color={"primary"}
                            disabled={!isConnected || tileSelection.amount === 0}
                            onClick={
                                () => {
                                    let tileIncrementName = null;
                                    if (hexGrid.selection !== null) {
                                        tileIncrementName = hexGrid.selection.image;
                                    }
                                    hexGrid.select(tileSelection.name);
                                    setTileNames([...tileNames].map(object => {
                                        let amount = object.amount;

                                        if (object.name === tileSelection.name) amount -= 1;

                                        if (object.name === tileIncrementName) amount += 1;

                                        return {
                                            ...object,
                                            amount: amount
                                        };
                                    }));
                                }
                            }>
                            <img src={srcName} alt="my image" width={60} height={60}/>
                        </IconButton>
                    </div>
                })
            }
        </div>
    </div>
}