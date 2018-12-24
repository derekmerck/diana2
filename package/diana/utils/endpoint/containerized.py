from time import sleep
import logging
import attr
import docker

@attr.s
class Containerized(object):
    """
    Many test fixtures create disposable Docker services to mock Diana platform
    connectivity.  These are managed through the Containerized class.  This class
    can be easily mixed into any endpoint, as demonstrated in the unit test suite.
    """

    dkr_client = None

    dkr_service = attr.ib(default="service")
    dkr_image   = attr.ib(default=None)
    dkr_ports   = attr.ib(factory=dict)
    dkr_command = attr.ib(default=None)
    dkr_env     = attr.ib(factory=dict)
    dkr_links   = attr.ib(factory=dict)
    dkr_remove  = attr.ib(default=True)

    dkr_container = attr.ib(init=False, repr=False)

    def start_service(self):
        """
        Run the dkr_image with appropriate configuration
        """
        logger = logging.getLogger(self.dkr_service)
        logger.info("Starting up service")

        if not Containerized.dkr_client:
            Containerized.dkr_client = docker.from_env()

        try:
            svc = Containerized.dkr_client.containers.get(self.dkr_service)
        except Exception:
            svc = Containerized.dkr_client.containers.run(image=self.dkr_image,
                                                          name=self.dkr_service,
                                                          command=self.dkr_command,
                                                          ports=self.dkr_ports,
                                                          links=self.dkr_links,
                                                          environment=self.dkr_env,
                                                          detach=True,
                                                          remove=self.dkr_remove)

        while svc.status != "running":
            svc.reload()
            sleep(1)

        self.dkr_container = svc

    def stop_service(self):
        """
        Stop the running container associated with this service.
        """

        logger = logging.getLogger(self.dkr_service)
        logger.info("Tearing down service")

        try:
            self.dkr_container.stop()
        except:
            logging.warning("Failed to stop service {}".format(self.dkr_service))
            pass
