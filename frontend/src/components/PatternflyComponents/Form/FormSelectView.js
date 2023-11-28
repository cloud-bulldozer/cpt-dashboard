import {FormSelect, FormSelectOption} from "@patternfly/react-core";


export const FormSelectView = ({onChange, options, selectedValue}) =>{
    return <>
        <FormSelect value={selectedValue} onChange={(e)=>onChange(e.target.value)} aria-label="FormSelect Input" ouiaId="BasicFormSelect">
          {options && options.map((value, index) => (
            <FormSelectOption key={index} value={value} label={value} />
          ))}
        </FormSelect>
    </>
}
