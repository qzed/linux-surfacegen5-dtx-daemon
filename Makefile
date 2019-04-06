.PHONY: all clean clean-all run run-pex install uninstall-most uninstall


all: surface-dtx-daemon.pex

surface-dtx-daemon.pex: $(wildcard dtx/*.py)
	$(eval DEPS:=$(shell env PIPENV_VENV_IN_PROJECT=1 pipenv lock -r | grep -v '^-i'))
	pex . ${DEPS} -e surface_dtx.daemon:run_app -o $@

clean:
	@rm -rf dtx/__pycache__
	@rm -rf surface_dtx.egg-info

clean-all: clean
	@rm -rf .venv
	@rm -f surface-dtx-daemon.pex

run:
	./surface-dtx-daemon -c ./etc/surface-dtx.cfg

run-pex:
	$(eval DEPS:=$(shell env PIPENV_VENV_IN_PROJECT=1 pipenv lock -r | grep -v '^-i'))
	pex . ${DEPS} -e surface_dtx.daemon:run_app -- -c ./etc/surface-dtx.cfg

install: surface-dtx-daemon.pex
	@echo "Installing app files to '${DESTDIR}/opt/surface-dtx/'."
	@mkdir -p "${DESTDIR}/opt/surface-dtx/"
	@cp "surface-dtx-daemon.pex" "${DESTDIR}/opt/surface-dtx/surface-dtx-daemon"
	@cp "LICENSE" "${DESTDIR}/opt/surface-dtx/"
	@cp "README.md" "${DESTDIR}/opt/surface-dtx/"

	@chmod 644 "${DESTDIR}/opt/surface-dtx/LICENSE"
	@chmod 644 "${DESTDIR}/opt/surface-dtx/README.md"
	@chmod 755 "${DESTDIR}/opt/surface-dtx/surface-dtx-daemon"

	@echo "Installing config files to '${DESTDIR}/etc/surface-dtx/'."
	@mkdir -p "${DESTDIR}/etc/surface-dtx/"
	@cp etc/* "${DESTDIR}/etc/surface-dtx/"

	@chmod 644 "${DESTDIR}/etc/surface-dtx/surface-dtx.cfg"
	@chmod 755 "${DESTDIR}/etc/surface-dtx/attach.sh"
	@chmod 755 "${DESTDIR}/etc/surface-dtx/detach.sh"

	@echo "Installing systemd unit file to '${DESTDIR}/usr/lib/systemd/system/surface-dtx.service'."
	@mkdir -p "${DESTDIR}/usr/lib/systemd/system/"
	@cp systemd/surface-dtx.service "${DESTDIR}/usr/lib/systemd/system/surface-dtx.service"

	@chmod 644 "${DESTDIR}/usr/lib/systemd/system/surface-dtx.service"

	@echo "Installation complete."
	@echo "    Don't forget to run 'systemctl enable surface-dtx.service'".

uninstall-core:
	@rm -rf ${DESTDIR}/opt/surface-dtx
	@rm -rf ${DESTDIR}/usr/lib/systemd/system/surface-dtx.service

uninstall: uninstall-core
	@rm -rf ${DESTDIR}/etc/surface-dtx
