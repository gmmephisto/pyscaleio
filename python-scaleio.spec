%if 0%{?fedora} > 12 || 0%{?rhel} > 7
%bcond_without python3
%else
%bcond_with python3
%endif

%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%endif
%if %{with python3}
%{!?__python3: %global __python3 /usr/bin/python3}
%{!?python3_sitelib: %global python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%endif  # with python3

%define  pkgname pyscaleio

Name:    python-scaleio
Version: 0.1.5
Release: 1%{?dist}
Summary: ScaleIO API client

Group:   Development/Tools
License: GPLv3
URL:     https://github.com/gmmephisto/pyscaleio
Source:  https://pypi.python.org/packages/source/p/%pkgname/%pkgname-%version.tar.gz

BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-six
BuildRequires: python-pbr
%if %{with python3}
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-six
BuildRequires: python3-pbr
%endif  # with python3

BuildArch:     noarch

Requires: python-requests >= 2.3
Requires: python-object-validator >= 0.1.4
Requires: python-psys >= 0.3
Requires: python-inflection
Requires: python-six

%description
Python library that provides convenient way to interact with ScaleIO REST API.


%if %{with python3}
%package -n python3-scaleio
Summary: ScaleIO API client

Requires: python3-requests >= 2.3
Requires: python3-object-validator >= 0.1.4
Requires: python3-psys >= 0.3
Requires: python3-inflection
Requires: python3-six

%description -n python3-scaleio
Python library that provides convenient way to interact with ScaleIO REST API.
%endif  # with python3


%prep
%setup -q -n %pkgname-%version


%build
PBR_VERSION=%version %{__python2} setup.py build
%if %{with python3}
PBR_VERSION=%version %{__python3} setup.py build
%endif  # with python3


%install
[ "%buildroot" = "/" ] || rm -rf "%buildroot"

PBR_VERSION=%version %{__python2} setup.py install --skip-build --root "%buildroot"
%if %{with python3}
PBR_VERSION=%version %{__python3} setup.py install --skip-build --root "%buildroot"
%endif  # with python3


%files
%defattr(-,root,root,-)
%{python2_sitelib}/pyscaleio
%{python2_sitelib}/pyscaleio-%{version}-*.egg-info
%doc ChangeLog README.rst

%if %{with python3}
%files -n python3-scaleio
%defattr(-,root,root,-)
%{python3_sitelib}/pyscaleio
%{python3_sitelib}/pyscaleio-%{version}-*.egg-info
%doc ChangeLog README.rst
%endif  # with python3


%clean
[ "%buildroot" = "/" ] || rm -rf "%buildroot"


%changelog
* Tue Jun 20 2017 Mikhail Ushanov <gm.mephisto@gmail.com> - 0.1.5-1
- New version.
- Python3 compatibility fixes.

* Wed Mar 29 2017 Mikhail Ushanov <gm.mephisto@gmail.com> - 0.1.4-1
- New version.
- Update requires version.

* Wed Apr 20 2016 Mikhail Ushanov <gm.mephisto@gmail.com> - 0.1.2-1
- New version.
- Update requires version.

* Tue Apr 19 2016 Mikhail Ushanov <gm.mephisto@gmail.com> - 0.1.1-1
- New version.
- Update spec.

* Tue Apr 12 2016 Mikhail Ushanov <gm.mephisto@gmail.com> - 0.0.1-1
- Initial build.
