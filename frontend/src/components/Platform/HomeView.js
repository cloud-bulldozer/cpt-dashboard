

import './PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import React, {useEffect} from 'react';
import {
    Gallery,
    GalleryItem
} from "@patternfly/react-core";
import {useDispatch, useSelector} from "react-redux";
import AccordionView from "./PatternflyComponents/Accordion/AccordionView";
import ListView from "./PatternflyComponents/List/ListView";
import CardView from "./PatternflyComponents/Card/CardView";
import {fetchAirflowData, fetchJenkinsData, fetchProwCIData} from "../../store/Actions/ActionCreator";


export default function HomeView() {
  const airflow = useSelector(state => state.airflow)
  const prowCi = useSelector(state => state.prowci)
  const jenkins =  useSelector(state => state.jenkins)

  const dispatch = useDispatch()

  useEffect(() => {
      const fetchData = async () =>{
          await dispatch(fetchAirflowData())
          await dispatch(fetchJenkinsData())
          await dispatch(fetchProwCIData())
      }
      fetchData()
    }, [dispatch])

  return (
    <>
        <Gallery hasGutter>
            {[airflow, prowCi, jenkins].map( (item , index) => {
                return <GalleryItem key={index}>
                    <CardView header={item.system} initialState={item.initialState}
                    body={<AccordionView childComponent={
                        <ListView list_view={[`Success: ${item.success}`, `Failure: ${item.failure}`,
                                             `Total: ${item.total}`]}/>
                    }/>}/>
                </GalleryItem>
            })}
        </Gallery>
    </>
  );
}
