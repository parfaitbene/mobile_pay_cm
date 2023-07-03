class ApiException(Exception):
    
    def __init__(self, message):
        """
        :param message: exception message and frontend modal content
        """
        super().__init__(message)
