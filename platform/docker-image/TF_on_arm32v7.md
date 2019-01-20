# Cross Compiling Tensorflow for Python 3.7 on Raspberry Pi

Merck, Winter 2019

The Diana docker-image is based on Debian-Buster, which uses Python 3.7.  Available TF builds for arm32v7 are based on Raspian9/Python 3.4.
 
Following recipe for building a TF wheel for Python 3.7 on a Raspberry Pi is based on modifying the workflow described at <https://www.tensorflow.org/install/source_rpi>.

## Change pointers from Trusty -> Disco 
```
$ TF_PATH=tensorflow/tools/ci_build
$ sed -i 's\trusty\disco\g' \
       $TF_PATH/Dockerfile.pi-python3 \
       $TF_PATH/install_python3_toolchain
```
Disco is based on Debian Buster and includes Python 3.7 by default.  References to Trusty are hardcoded into the base Dockerfile and the python3 toolchain installation.  The deb installation script does dynamic version discovery.

## Dockerfile.pi-python3
-> Remove backports repos
```
#RUN add-apt-repository -y ppa:openjdk-r/ppa && \
#    add-apt-repository -y ppa:george-edison55/cmake-3.x
```
-> Remove Python 2.7 `python-.\*` packages
-> Add `python3-pip` package 

## install/install_deb_packages.sh
-> Remove `apt-key` line
-> Edit clang-format-3.8 -> clang-format
```
$ sed 's\^apt-key/#&/' $TF_PATH/install/install_deb_packages.sh
$ sed 's\clang-format-3.8/clang-format/' $TF_PATH/install/install_deb_packages.sh
```

## install/install_pip_packages.sh
-> Remove easy_install pip because we used apt and have a more recent pip already
-> Remove _all_ `pip2` references
```
$ sed 's\^easy_install/#&/g' $TF_PATH/install/install_pip_packages.sh
$ sed 's\^pip2/#&/g' $TF_PATH/install/install_pip_packages.sh
```
^^^ This misses one with some white space at the beginning of the line
-> Remove version requirements for `scikit-learn`, `scipy`, `numpy`, `pandas` so it uses recent wheels rather than compiling the older packages specified


## pi/build_raspberrypi.sh
-> Fix curl header location (and file name)
```
$ sed 's\/usr/include/curlbuild.h\/usr/include/x86_64-linux-gnu/curl/system.h\g' $TF_PATH/pi/build_raspberry_pi.sh
```

## Run it
-> Change crosstools include path to point at Python 3.7
```
$ CI_DOCKER_EXTRA_PARAMS="-e CI_BUILD_PYTHON=python3 -e CROSSTOOL_PYTHON_INCLUDE_PATH=/usr/include/python3.7" \
    tensorflow/tools/ci_build/ci_build.sh PI-PYTHON3 \
    tensorflow/tools/ci_build/pi/build_raspberry_pi.sh
```

Compilation takes about 20 minutes.


## Acknowledgments

Thanks again to [Packet][]'s affiliated [Works On Arm][] program for providing compute time for developing and testing this workflow.

[Packet.net]: https://packet.net
[Works On Arm]: https://www.worksonarm.com


