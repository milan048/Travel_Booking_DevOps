# Travel Booking System

Simple Flask travel booking application adapted for a college DevOps project.

See [README_DEVOPS.md](README_DEVOPS.md) for Docker, Jenkins, Kubernetes, monitoring, logging and security instructions.


## Fresh checkout behavior
On first startup the app automatically creates demo flights, hotels and package deals so the search pages are usable without manually entering database records. Registration also requires the `email-validator` dependency included in `requirements.txt`.
