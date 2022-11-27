
def initPlugin() -> None:
	from model.commands import parser, argumentContextsImpl

	from sessionOld.session import getSession
	setGetSession(getSession)


def setGetSession(getSession):
	from . import validator
	validator.getSession = getSession
