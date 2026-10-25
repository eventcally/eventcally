from project.infrastructure.event_handler_factory import EventHandlerFactory


def test_call_delegates_to_the_factory_aggregate(mocker):
    aggregate = mocker.Mock(return_value=["handler"])
    event_type = mocker.Mock()

    assert EventHandlerFactory(aggregate)(event_type) == ["handler"]
    aggregate.assert_called_once_with(event_type)
