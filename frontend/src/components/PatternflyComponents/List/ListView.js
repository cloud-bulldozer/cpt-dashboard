import {List, ListItem} from "@patternfly/react-core";

export const ListView = ({list_view = []}) => {
    return (
        <List>
            {list_view &&
                list_view.map(
                    (value, index) => <ListItem key={index}>{value}</ListItem>
                )
            }
        </List>
    )
}
export default ListView;
