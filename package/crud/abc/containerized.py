from abc import ABC
from time import sleep
import logging
import attr
import docker

@attr.s
class Containerized(ABC):
    """
    It can be useful for an endpoint to be able to instantiate a backend
    service from its own state dictionary.

    This class can be easily mixed into any endpoint, as demonstrated in the
    unit test suite.   Many of the unit test fixtures create disposable Docker
    services to mock platform connectivity.

    Includes methods for starting containers and swarm services.
    """

    dkr_name    = attr.ib(default="Endpoint")
    dkr_image   = attr.ib(default=None)
    dkr_ports   = attr.ib(factory=dict)
    dkr_command = attr.ib(default=None)
    dkr_env     = attr.ib(factory=dict)
    dkr_links   = attr.ib(factory=dict)
    dkr_remove  = attr.ib(default=True)

    dkr_container = attr.ib(init=False, repr=False)
    dkr_service = attr.ib(init=False, repr=False)

    def start_container(self):
        """
        Run the dkr_image as a container with appropriate configuration
        """
        logger = logging.getLogger(self.dkr_name)
        logger.info("Starting up container")

        try:
            svc = self.docker_client().containers.get(self.dkr_name)
        except Exception:
            svc = self.docker_client().containers.run(image=self.dkr_image,
                                                      name=self.dkr_name,
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

    def stop_container(self):
        """
        Stop the running container associated with this endpoint.
        """

        logger = logging.getLogger(self.dkr_name)
        logger.info("Tearing down container")

        try:
            self.dkr_container.stop()
        except:
            logging.warning("Failed to stop service {}".format(self.dkr_name))
            pass

    def start_service(self):
        """
        Run the dkr_image as a swarm service with appropriate configuration
        """
        logger = logging.getLogger(self.dkr_name)
        logger.info("Starting up service")

        self.start_swarm()

        container_spec = docker.types.ContainerSpec(
            image=self.dkr_image,
            command=self.dkr_command,
            env=self.dkr_env
        )
        task_tmpl = docker.types.TaskTemplate(container_spec)
        svc = self.api_client().create_service(
            name=self.dkr_name,
            task_template=task_tmpl)

        self.dkr_service = svc

    def stop_service(self):
        """
        Stop the running swarm service associated with this endpoint.
        """

        logger = logging.getLogger(self.dkr_name)
        logger.info("Tearing down service")

        try:
            self.dkr_service.remove()
        except:
            logging.warning("Failed to stop service {}".format(self.dkr_name))
            pass

    _docker_client = None
    @classmethod
    def docker_client(cls):
        if not cls._docker_client:
            logging.info("Getting Docker client")
            cls._docker_client = docker.from_env()
        return cls._docker_client

    _api_client = None
    @classmethod
    def api_client(cls):
        if not cls._api_client:
            logging.info("Getting Docker API client")
            cls._api_client = docker.APIClient()
        return cls._api_client

    _swarm_started = False
    @classmethod
    def start_swarm(cls):
        if not cls._swarm_started:
            try:
                logging.info("Currently in swarm")
                info = cls.api_client().inspect_swarm()
                logging.debug(info)
            except docker.errors.APIError:
                logging.info("Starting new swarm")
                info = cls.api_client().init_swarm()
                logging.debug(info)
        cls._swarm_started = True

    @classmethod
    def clean_swarm(cls):
        for item in cls.api_client().services():
            cls.api_client().remove_service(item['ID'])
