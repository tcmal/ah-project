from tkinter.ttk import Button

# Convenience mixin to add back button to view
class ViewHasBackButton:
	def add_back_button(self, *args, **kwargs):
		Button(self.frame, text="Back", command=self.back_home).grid(*args, **kwargs)

	def back_home(self):
		from views import HomeView
		self.app.replace_view(HomeView)