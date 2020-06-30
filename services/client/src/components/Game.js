import React, {useEffect, useState} from 'react';
import {HexGrid} from "./HexGrid";
import { Button } from "@material-ui/core";

function TileSelection(name, amount) {
    this.name = name;
    this.amount = amount;
}

let hexGrid = new HexGrid();
// Initialize event handlers for mouse.
document.addEventListener('mousedown', (ev) => hexGrid.handleMouseDown(ev));
document.addEventListener('mousemove', (ev) => hexGrid.handleMouseMove(ev));
document.addEventListener('mouseup', (ev) => hexGrid.handleMouseUp(ev));

export default function Game() {
    let board = React.useRef(null);
    const [tileNames, setTileNames] = useState([
        new TileSelection("ladybug", 3),
        new TileSelection("queen", 1)
    ]);

    useEffect(() => {
        // Register canvas and load resources.
        hexGrid.setCanvas(board.current);
        hexGrid.preloadResources();

        setInterval(() => hexGrid.update(), 1000/60);
    }, []);

    return <div className={"content-wrapper"}>
        <canvas ref={board} className={"canvas"}>
        </canvas>
        <div className={"tile-selection"}>
            {
                tileNames.map((tileSelection, i) => {
                    let srcName = "static/images/" + tileSelection.name + ".png";
                    return <div key={i}>
                        <div>{tileSelection.amount} tiles left.</div>
                        <button disabled={tileSelection.amount === 0}>
                            <img src={srcName} alt="my image" onClick={
                                () => {
                                    hexGrid.select(tileSelection.name);
                                    setTileNames([...tileNames].map(object => {
                                        if (object.name === tileSelection.name) {
                                            return {
                                                ...object,
                                                amount: object.amount-1
                                            }
                                        } else return object;
                                    }));
                                }
                            } width={80} height={80}/>
                        </button>
                    </div>
                })
            }
        </div>
    </div>
}