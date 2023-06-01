from examples.readme_usage import odyssey


async def test_gives_expected_logs(capsys):
    await odyssey()
    assert capsys.readouterr().out == """odysseus is in danger from Zeus' lightning bolt!
odysseus's health dropped to 77
odysseus is in danger from Poseidon's storm!
odysseus's health dropped to 63
but athena intervened saving and healing odysseus to 100
odysseus is in danger from Poseidon's storm!
odysseus's health dropped to 78
odysseus is in danger from Poseidon's storm!
odysseus's health dropped to 65
odysseus is in danger from Poseidon's storm!
odysseus's health dropped to 42
odysseus is in danger from Poseidon's storm!
odysseus's health dropped to 42
odysseus is in danger from Zeus' lightning bolt!
odysseus's health dropped to 30
odysseus is in danger from Poseidon's storm!
odysseus's health dropped to 0
odysseus died
athena was too late to save odysseus
"""

    
