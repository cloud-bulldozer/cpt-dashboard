import './App.css';
import './fonts.css';
import "@patternfly/react-core/dist/styles/base.css";

// import components
import OcpPerformanceApp from './components/OcpPerformanceApp';

// import fake data
import { ocpdata, ocpdata2 } from './mocks';

function App() {
  return (
    <div className="App">
      <OcpPerformanceApp data={ocpdata2}/>
    </div>
  );
}

export default App;
