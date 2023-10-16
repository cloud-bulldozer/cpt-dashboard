import {Toolbar, ToolbarGroup, ToolbarItem} from "@patternfly/react-core";
import React, {useEffect, useState} from "react";
import {Text4} from "../PatternflyComponents/Text/Text";
import {useSelector} from "react-redux";
import {Link} from "react-router-dom";


export const ToolBar = () => {

    const [active, setActive] = useState('home')

    useEffect(()=>{
        const path = window.location.href.split('/')
        let pathName = path[path.length-1]
        if(pathName==='') pathName='home'
        setActive(pathName)
    }, [])

    const linkStyle = (value) => {
        const styles = {}
        if(active === value) {
            styles['color'] = 'white'
            styles['borderBottom'] = '2px solid red'
        }
        return styles

    }



    const NavItems = (<>
        <ToolbarItem>
          <Link to="/" children={"Home"} style={linkStyle('home')} onClick={()=>setActive("home")}/>
        </ToolbarItem>
    </>)

    const job_results = useSelector(state => state.jobs)

    return <>
        <Toolbar id="toolbar" isFullHeight={true} isStatic={true}>
            <ToolbarGroup>
                <ToolbarItem>
                    <Text4 style={{color: '#FFFFFF'}} value="OCP PerfScale Dashboard" />
                </ToolbarItem>
                {NavItems}
                <ToolbarItem align={{ default: 'alignRight' }}>
                    <Text4 style={{color: "#FFFFFF"}} value={`Last Updated Time | ${job_results.updatedTime}`} />
                </ToolbarItem>
            </ToolbarGroup>
        </Toolbar>
    </>
}
