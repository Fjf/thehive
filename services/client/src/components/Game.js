import React, { useEffect } from 'react';
import {HexGrid} from "./HexGrid";
import { Button } from "@material-ui/core";

export default function Game() {
    let board = React.useRef(null);

    let hexGrid = new HexGrid();
    useEffect(() => {
        // Initialization
        document.addEventListener('mousedown', (ev) => hexGrid.handleMouseDown(ev));
        document.addEventListener('mousemove', (ev) => hexGrid.handleMouseMove(ev));
        document.addEventListener('mouseup', (ev) => hexGrid.handleMouseUp(ev));

        hexGrid.setCanvas(board.current);
        hexGrid.preloadImages();

        hexGrid.addImage("ladybug", 0, 0);
        hexGrid.addImage("queen", 1, 1);

        setInterval(() => hexGrid.update(), 1000/60);
    }, []);

    return <div className={"content-wrapper"}>
        <canvas ref={board} className={"canvas"}>
        </canvas>
        <Button onClick={() => {hexGrid.update()}}>Update</Button>
    </div>
}