export function getBuildLink(benchmarkConfigs) {
    var icon = "assets/images/jenkins-icon.svg"
    if (benchmarkConfigs.ciSystem === "PROW") {
        icon = "assets/images/prow-icon.png"
    }
    return <a href={benchmarkConfigs.build_url != '' && benchmarkConfigs.build_url || benchmarkConfigs.buildUrl} target={"_blank"}>
    <img src={icon}
        style={{width:'25px',height:'25px'}} />
</a>
}