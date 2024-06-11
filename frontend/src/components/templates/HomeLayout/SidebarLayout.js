import {Split, Stack, StackItem} from "@patternfly/react-core";
import {Text4} from "../../PatternflyComponents/Text/Text";
import {DatePickerView} from "../../PatternflyComponents/Date/DatePickerView";
import CardView from "../../PatternflyComponents/Card/CardView";
import {FormSelectView} from "../../PatternflyComponents/Form/FormSelectView";
import PropTypes from "prop-types";


export const SidebarLayout = ({sidebarComponents}) => {

    const DisplayDate = ({startDate, endDate, setStartDate,  setEndDate}) => {
        const dateView = (name, dateValue, onChange) => {
            return <Stack>
                        <StackItem children={<Text4 value={name}/>}/>
                        <StackItem children={<DatePickerView defaultDate={dateValue} setDate={onChange}/>}/>
                    </Stack>
        }

        return <>
            <Split hasGutter isWrappable>
                { dateView("Start Date", startDate, setStartDate) }
                { dateView("End Date", endDate, setEndDate) }
            </Split>
        </>
    }

    return <>
        <Stack hasGutter>
        {

            sidebarComponents && sidebarComponents.map( (component, index) => {
                if(component.name === "DateComponent") {
                    return <StackItem span={3} key={index} children={
                        <CardView body={<DisplayDate startDate={component.startDate}
                                                     setStartDate={component.setStartDate}
                                                     endDate={component.endDate} setEndDate={component.setEndDate} />}
                        />
                    } />
                }
                else{
                     return <StackItem key={index}
                                       children={<CardView initialState={false}
                                                           header={<Text4 value={component.name} />}
                                           body={<FormSelectView options={component.options}
                                                                 onChange={component.onChange}
                                                                 selectedValue={component.value}
                                           />}
                                />} />
                }
            })
        }
        </Stack>
    </>
}


SidebarLayout.propTypes = {
    sidebarComponents: PropTypes.arrayOf(
        PropTypes.shape({
            name: PropTypes.string.isRequired,
            options: PropTypes.array.isRequired,
            onChange: PropTypes.func,
            value: PropTypes.string,
            startDate: PropTypes.string,
            endDate: PropTypes.string,
            setStartDate: PropTypes.func,
            setEndDate: PropTypes.func
        })
    ).isRequired
}
