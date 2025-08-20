# ArgoCD

This helm chart deploys ArgoCD "Application" manifests into a cluster's argocd
namespace for the "dashboard" and "dashboard-dev" applications.

Both applications refer to the "deploy" chart to define the deployment.

To "prime" a cluster for the CPT Dashboard, you need to have ArgoCD (upstream)
or OpenShift GitOps (downstream) installed along with the [Argo CD Image
Updater](https://argocd-image-updater.readthedocs.io/en/stable/).

1. If you're using the upstream ArgoCD, you'll need to edit the `values.yaml`
file to set the `argocd.namespace` to `argocd` instead of `openshift-gitops`.
2. Set the `cluster` variable in `values.yaml` to the base URL path where the
dashboard should be exposed. The final URLs will be `dashboard.<cluster>` and
`dashboard-dev.<cluster>`.
3. Create the `dashboard` and `dashboard-dev` namespaces using the
`oc new-project <name>` command. Using `new-project` rather than
`create namespace` ensures that the proper OpenShift attributes are applied to
allow ArgoCD to manage resources within the namespace.
4. Use the `helm install dashboard ./argocd` command to install a Helm
`dashboard` "release" containing two ArgoCD Application resources, for the
production dashboard and the development dashboard. Note that, in the `values.yaml`,
either deployment can be disabled by setting the `enabled` value to `false`.
You can override values referenced in the chart using `--set <key>=<value>`;
for example `--set cluster=apps.mydomain.com`.
