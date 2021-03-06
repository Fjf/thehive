import React, {useEffect, useState} from 'react';
import {TextField} from '@material-ui/core';
import {HexGrid} from "./HexGrid";
import {useCookies} from 'react-cookie';
import socketIOClient from "socket.io-client";
import Button from "@material-ui/core/Button";
import Chat from "./Chat";
import IconButton from "@material-ui/core/IconButton";
import UserList from "./UserList";
import {userService} from "./userService";

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

    const [cookies, setCookie, removeCookie] = useCookies(['room']);
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
        let rm = cookies.room;
        if (rm !== undefined) {
            setRoom(rm);
        }
    }, []);

    function buttonDisconnectGame() {
        let username = userService.getUser().name;
        socket.emit("leave", {room: room, username: username});
        setRoom("");
        setIsConnected(false);
    }

    function buttonConnectGame() {
        // Reconnect socket to ensure correct login is used.
        socket.disconnect();
        socket.connect();
        connectGame(room);
    }

    function connectGame(room) {
        if (room === "") {
            return;
        }

        setCookie("room", room, {sameSite: "strict"});

        let username = userService.getUser().name;
        hexGrid.username = username;

        // Setup game_socket event listeners and join the selected room.
        socket.emit("join", {
            room: room
        });

        socket.on("userList", (response) => {
            if (response.length > 0)
                hexGrid.player1 = response[0].name;
            if (response.length > 1)
                hexGrid.player2 = response[1].name;
        });

        socket.on("boardState", (rawResponse) => {
            let response = JSON.parse(rawResponse);
            hexGrid.setBoardState(response);
        });

        socket.on("tileAmounts", (response) => {
            setTileNames(response);
        });

        socket.on("finished", (response) => {
            if (response.winner === username) {
                hexGrid.audio_files["success"].currentTime = 0.0;
                hexGrid.audio_files["success"].play();
            } else if (response.loser === username) {
                hexGrid.audio_files["incorrect"].currentTime = 0.0;
                hexGrid.audio_files["incorrect"].play();
            }
        });

        socket.on("placeTile", (response) => {
            hexGrid.audio_files["tile_sound_2"].currentTime = 0.0;
            hexGrid.audio_files["tile_sound_2"].play();

            hexGrid.markedTiles = [];
            let data = response.data;

            // Create a tile on desired position
            let tile;
            // Either it is player1, or you are playing, and it is your tile.

            if (response.username === hexGrid.player1) {
                // Place my tile
                tile = hexGrid.makeTile(data.image, data.x, data.y, hexGrid.tileClickHandler);
                tile.owner = response.username;
                tile.z = data.z;
                tile.mine = response.username === username;
            } else {
                // Place opponents tile.
                tile = hexGrid.makeTile(data.image, data.x, data.y, hexGrid.tileClickHandler);
                tile.z = data.z;
                tile.owner = response.username;
                tile.mine = response.username === username;
            }

            // Send information when you are one of the players.
            if (response.username === username) {
                // Remove tile from cursor.
                hexGrid.selection = null;

                // Notify other users that tile hover is no longer necessary to render.
                socket.emit("mouseHover", {
                    room: room,
                    username: username,
                    data: undefined
                })
            }

            hexGrid.putTile(tile, data.x, data.y);


        });

        socket.on("markedTiles", (rawResponse) => {
            hexGrid.markedTiles = JSON.parse(rawResponse);
        });

        hexGrid.onTilePlaceHandler = (tile) => {
            socket.emit("placeTile", {
                room: room,
                username: username,
                data: tile
            });
        };

        socket.on("pickupTile", (response) => {
            hexGrid.audio_files["tile_sound_2"].currentTime = 0.0;
            hexGrid.audio_files["tile_sound_2"].play();

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

        socket.on("mouseHover", (response) => {
            // Remotely sent tiles are never your own.
            // For the players themselves, always show as enemy hover.
            if (hexGrid.player1 === username || hexGrid.player2 === username) {
                hexGrid.setEnemyHover(response.data);
                return
            }
            // Spectators can see both colours.
            if (response.username === hexGrid.player2) {
                hexGrid.setEnemyHover(response.data);
            } else if (response.username === hexGrid.player1) {
                hexGrid.setHover(response.data);
            }
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

        setInterval(() => { socket.emit("getBoard", {room: room}); }, 1000/30);

        setIsConnected(true);
    }

    function unselect() {
        if (hexGrid.selection === null) return;

        setTileNames([...tileNames].map(object => {
            let amount = object.amount;

            if (object.name === hexGrid.selection.image) amount += 1;

            return {
                ...object,
                amount: amount
            };
        }));

        hexGrid.selection = null;
    }

    return <div
        className={"content-wrapper"}
        tabIndex={"0"}
        onKeyDown={(ev) => {
            console.log(ev.key);
            if (ev.key === "Escape") unselect();
        }}>
        <div className={"left-menu-column"}>
            <div className={"column-data"}>
                {isConnected ? "Connected" : "Disconnected"}
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
            <UserList data={{
                socket: socket,
                room: room
            }}/>
            <Chat data={{
                ...chatData,
                room: room
            }}/>
        </div>
        <div className={"main-content-wrapper"}>
            <div className={"canvas-wrapper"}>
                <canvas ref={board} className={"canvas"} id={"canvas"}>
                </canvas>
                <a href={"https://www.ultraboardgames.com/hive/game-rules.php"} target="_blank">Rules</a>
            </div>
            <div id={"tile-selection"}>
                {
                    tileNames.map((tileSelection, i) => {
                        let srcName = "static/images/" + tileSelection.name + ".png";
                        return <div key={i}>
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
                            <div>{tileSelection.amount} {tileSelection.name}{tileSelection.amount !== 1 ? "s" : ""} left.</div>
                        </div>
                    })
                }
            </div>
        </div>
    </div>
}