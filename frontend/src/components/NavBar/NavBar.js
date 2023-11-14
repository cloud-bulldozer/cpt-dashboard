import {
    Brand,
    Icon,
    Masthead,
    MastheadBrand,
    MastheadContent,
    MastheadMain,
} from "@patternfly/react-core";

import "../css/NavBar.css"
import {ToolBar} from "./ToolBar";
import React from "react";

export const NavBar = ({fixed=false}) => {
    return <>
        <Masthead>
            <MastheadMain>
                <MastheadBrand href={"/home"}>
                    <Icon size={"xl"} >
                        <Brand src={"logo.png"} alt="CPT-Dashboard"/>
                    </Icon>
                </MastheadBrand>
            </MastheadMain>
            <MastheadContent>
                <ToolBar />
            </MastheadContent>
        </Masthead>
    </>
}
